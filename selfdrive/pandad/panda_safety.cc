#include "selfdrive/pandad/pandad.h"
#include "cereal/messaging/messaging.h"
#include "common/swaglog.h"
#include "json11.hpp"

#include <unordered_set>

static bool isVwMebMqbevoPlatform(const std::string &platform) {
  static const std::unordered_set<std::string> platforms = {
    "VOLKSWAGEN_ID3_MK1", "VOLKSWAGEN_ID3_MK2",
    "VOLKSWAGEN_ID4_MK1", "VOLKSWAGEN_ID4_MK2",
    "VOLKSWAGEN_GOLF_MK8",
    "AUDI_Q4_MK1", "AUDI_Q4_MK2",
    "CUPRA_BORN_MK1",
    "SKODA_ENYAQ_MK1", "SKODA_ENYAQ_MK2",
    "SEAT_LEON_MK4",
  };
  return platforms.count(platform) > 0;
}

void PandaSafety::configureSafetyMode(bool is_onroad) {
  // Bring CAN FD up for VW MEB/MQBevo before the car is identified (see ensureCanFdForCachedMeb).
  ensureCanFdForCachedMeb();

  if (is_onroad && !safety_configured_) {
    updateMultiplexingMode();

    auto car_params = fetchCarParams();
    if (!car_params.empty()) {
      LOGW("got %lu bytes CarParams", car_params[0].size());
      LOGW("got %lu bytes IQCarParams", car_params[1].size());
      setSafetyMode(car_params);
      safety_configured_ = true;
    }
  } else if (!is_onroad) {
    initialized_ = false;
    safety_configured_ = false;
    log_once_ = false;
  }
}

void PandaSafety::updateMultiplexingMode() {
  // Initialize to ELM327 without OBD multiplexing for initial fingerprinting
  if (!initialized_) {
    prev_obd_multiplexing_ = false;
    for (int i = 0; i < pandas_.size(); ++i) {
      pandas_[i]->set_safety_model(cereal::CarParams::SafetyModel::ELM327, 1U);
    }
    initialized_ = true;
  }

  // Switch between multiplexing modes based on the OBD multiplexing request
  bool obd_multiplexing_requested = params_.getBool("ObdMultiplexingEnabled");
  if (obd_multiplexing_requested != prev_obd_multiplexing_) {
    for (int i = 0; i < pandas_.size(); ++i) {
      const uint16_t safety_param = (i > 0 || !obd_multiplexing_requested) ? 1U : 0U;
      pandas_[i]->set_safety_model(cereal::CarParams::SafetyModel::ELM327, safety_param);
    }
    prev_obd_multiplexing_ = obd_multiplexing_requested;
    params_.putBool("ObdMultiplexingChanged", true);
  }
}

// TODO-IQ: Use structs instead of vector
std::vector<std::string> PandaSafety::fetchCarParams() {
  if (!params_.getBool("FirmwareQueryDone")) {
    return {};
  }

  if (!log_once_) {
    LOGW("Finished FW query, Waiting for params to set safety model");
    log_once_ = true;
  }

  if (!params_.getBool("ControlsReady")) {
    return {};
  }
  return {params_.get("CarParams"), params_.get("IQCarParams")};
}

// TODO-IQ: Use structs instead of vector
void PandaSafety::setSafetyMode(const std::vector<std::string> &params_string) {
  AlignedBuffer aligned_buf;
  AlignedBuffer aligned_buf_iq;

  capnp::FlatArrayMessageReader cmsg(aligned_buf.align(params_string[0].data(), params_string[0].size()));
  cereal::CarParams::Reader car_params = cmsg.getRoot<cereal::CarParams>();

  capnp::FlatArrayMessageReader cmsg_iq(aligned_buf_iq.align(params_string[1].data(), params_string[1].size()));
  cereal::IQCarParams::Reader car_params_iq = cmsg_iq.getRoot<cereal::IQCarParams>();

  auto safety_configs = car_params.getSafetyConfigs();
  uint16_t alternative_experience = car_params.getAlternativeExperience();
  uint16_t safety_param_iq = car_params_iq.getSafetyParam();

  for (int i = 0; i < pandas_.size(); ++i) {
    // Default to SILENT safety model if not specified
    cereal::CarParams::SafetyModel safety_model = cereal::CarParams::SafetyModel::SILENT;
    uint16_t safety_param = 0U;
    if (i < safety_configs.size()) {
      safety_model = safety_configs[i].getSafetyModel();
      safety_param = safety_configs[i].getSafetyParam();
    }

    LOGW("Panda %d: setting safety model: %d, param: %d, alternative experience: %d, param_iq: %d", i, (int)safety_model, safety_param, alternative_experience, safety_param_iq);
    pandas_[i]->set_alternative_experience(alternative_experience, safety_param_iq);
    pandas_[i]->set_safety_model(safety_model, safety_param);
  }
}

void PandaSafety::ensureCanFdForCachedMeb() {
  // VW MEB / MQBevo have no ignition line — ignition is the 0x3C0 CAN message on the CAN FD
  // powertrain bus. The real car safety model is only set onroad (setSafetyMode, gated on
  // FirmwareQueryDone + ControlsReady), but going onroad needs ignition, so CAN FD must already
  // be up while still offroad/noOutput. The panda zeroes can_data_speed on every safety-model
  // change until a bus is explicitly requested via 0xf9, so request FD here from either the
  // UI-selected CarPlatformBundle or the cached CarParams. Gated on MEB/MQBevo only, and the
  // panda latches the request (canfd_requested) so it survives subsequent safety-model changes.
  if (canfd_configured_) {
    return;
  }

  bool is_meb = false;
  const char *source = nullptr;

  // Method A: UI manual platform selection (e.g. Volkswagen ID.3 2024-25 → VOLKSWAGEN_ID3_MK2)
  std::string bundle_bytes = params_.get("CarPlatformBundle");
  if (!bundle_bytes.empty()) {
    std::string err;
    json11::Json bundle = json11::Json::parse(bundle_bytes, err);
    if (err.empty() && bundle.is_object()) {
      std::string platform = bundle["platform"].string_value();
      if (isVwMebMqbevoPlatform(platform)) {
        is_meb = true;
        source = "bundle";
      } else {
        canfd_configured_ = true;  // manual selection is a non-MEB platform
        return;
      }
    }
  }

  // Method B: cached car fingerprint (CarParamsPersistent)
  if (!is_meb) {
    std::string cp_bytes = params_.get("CarParamsPersistent");
    if (cp_bytes.empty()) {
      return;  // no cache yet (e.g. first-ever setup) — retry next loop
    }

    AlignedBuffer aligned_buf;
    capnp::FlatArrayMessageReader cmsg(aligned_buf.align(cp_bytes.data(), cp_bytes.size()));
    cereal::CarParams::Reader car_params = cmsg.getRoot<cereal::CarParams>();

    auto safety_configs = car_params.getSafetyConfigs();
    for (int i = 0; i < safety_configs.size(); ++i) {
      auto model = safety_configs[i].getSafetyModel();
      if ((model == cereal::CarParams::SafetyModel::VOLKSWAGEN_MEB) ||
          (model == cereal::CarParams::SafetyModel::VOLKSWAGEN_MQB_EVO)) {
        is_meb = true;
        source = "cache";
        break;
      }
    }

    if (!is_meb) {
      canfd_configured_ = true;  // cached params exist but not MEB/MQBevo
      return;
    }
  }

  if (is_meb) {
    for (int i = 0; i < pandas_.size(); ++i) {
      for (uint16_t bus = 0U; bus < 3U; ++bus) {
        pandas_[i]->set_data_speed_kbps(bus, 2000);  // 2 Mbps CAN FD data phase
      }
    }
    LOGW("VW MEB: requested CAN FD (2Mbps) on Bus 0/1/2 for pre-ignition CAN FD (%s)", source);
    canfd_configured_ = true;
  }
}

bool PandaSafety::getOffroadMode() {
  auto offroad_mode = params_.getBool("OffroadMode");
  return offroad_mode;
}
