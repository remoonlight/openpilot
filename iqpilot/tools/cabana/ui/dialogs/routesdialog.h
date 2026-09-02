#pragma once

#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "tools/cabana/routes.h"
#include "tools/cabana/ui/util.h"


class RoutesDialog {
public:
  void open(std::function<void(bool accepted, const std::string &route)> on_done);
  void draw();

private:
  void setDeviceList(const std::vector<routes::DeviceInfo> &devices, bool success, int error_code);
  void setRouteList(const std::vector<routes::RouteInfo> &list, bool success);
  void fetchRoutes();
  void finish(bool accepted);

  struct RouteItem {
    std::string label;
    std::string name;
  };

  struct State {
    bool devices_loaded = false;
    std::vector<std::string> devices;
    int device_index = 0;
    int period_index = 0;
    std::vector<RouteItem> routes;
    int route_index = -1;
    std::string empty_text = "No items";
    int fetch_id = 0;
  };

  bool open_ = false;
  PopupOwner popup_;
  State s_;
  std::function<void(bool, const std::string &)> on_done_;

  std::shared_ptr<bool> alive_;
};
