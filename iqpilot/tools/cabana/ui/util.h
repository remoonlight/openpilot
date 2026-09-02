#pragma once

#include <functional>
#include <string>
#include <vector>

#include "imgui.h"
#include "imgui_internal.h"

#include "tools/cabana/core/color.h"
#include "tools/cabana/utils/util.h"

struct GLFWwindow;

inline ImVec4 colorRgb(int r, int g, int b, float alpha = 1.0f) {
  return ImVec4(r / 255.0f, g / 255.0f, b / 255.0f, alpha);
}

inline ImU32 toImU32(const CabanaColor &c) { return IM_COL32(c.r, c.g, c.b, c.a); }
inline ImVec4 toImVec4(const CabanaColor &c) { return ImVec4(c.r / 255.0f, c.g / 255.0f, c.b / 255.0f, c.a / 255.0f); }
inline ImU32 withAlpha(ImU32 c, int alpha) { return (c & ~IM_COL32_A_MASK) | ((ImU32)alpha << IM_COL32_A_SHIFT); }


constexpr const char *MESSAGES_PANEL_ID = "###MessagesPanel";

struct InputContext {
  std::string *str;
  ImGuiInputTextCallback validator;
  ValidState (*validate)(const std::string &) = nullptr;
  const std::string *last_valid = nullptr;
};

int inputCallback(ImGuiInputTextCallbackData *data);


bool validatedInput(const char *label, std::string *s, ImGuiInputTextCallback validator, const char *hint = "",
                    ImGuiInputTextFlags flags = 0);

inline bool inputText(const char *label, std::string *s, const char *hint = "", ImGuiInputTextFlags flags = 0) {
  return validatedInput(label, s, nullptr, hint, flags);
}

bool inputTextMultiline(const char *label, std::string *s, const ImVec2 &size, ImGuiInputTextFlags flags = 0);


bool clearableInput(const char *label, std::string *s, const char *hint = "", ImGuiInputTextCallback validator = nullptr);

bool comboBox(const char *label, int *index, const std::vector<std::string> &items);


template <typename T>
inline bool comboBox(const char *label, int *index, const T *values, int count) {
  bool changed = false;
  const std::string preview = *index >= 0 && *index < count ? std::to_string(values[*index]) : "";
  if (ImGui::BeginCombo(label, preview.c_str())) {
    for (int i = 0; i < count; ++i) {
      ImGui::PushID(i);
      if (ImGui::Selectable(std::to_string(values[i]).c_str(), i == *index) && *index != i) {
        *index = i;
        changed = true;
      }
      if (i == *index) ImGui::SetItemDefaultFocus();
      ImGui::PopID();
    }
    ImGui::EndCombo();
  }
  return changed;
}


bool validatedText(const char *label, std::string *s, ValidState (*validate)(const std::string &),
                   const char *hint = "", ImGuiInputTextCallback filter = nullptr);


int nameValidator(ImGuiInputTextCallbackData *data);
int nodeValidator(ImGuiInputTextCallbackData *data);
int doubleValidator(ImGuiInputTextCallbackData *data);
int ipValidator(ImGuiInputTextCallbackData *data);
int nonWhitespaceValidator(ImGuiInputTextCallbackData *data);


bool toolButton(const char *id, const char *icon, const char *tooltip = nullptr, const char *text = nullptr);


void disabledItemTooltip(const char *text);



bool radioMenuItem(const char *label, bool checked, float width = 0.0f);




struct PopupOwner {
  ImGuiID popup_id = 0, owner_id = 0;


  bool begin(const char *id);

  void reset() { popup_id = owner_id = 0; }
};


bool dialogEscapePressed();


ImGuiWindow *topPopupWindow();


bool dialogButtons(const char *accept_label, bool *accepted, bool *rejected, bool accept_enabled = true,
                   const char *reject_label = "Cancel");


int tableHeadersRow();




bool viewSelectable(const char *label, bool selected, ImGuiSelectableFlags flags, const ImVec2 &size);



bool checkBox(const char *label, bool *v);


void alignRight(float width);


void drawText(ImDrawList *dl, const ImRect &rect, const char *text, ImU32 col, ImFont *font = nullptr,
              float font_size = 0.0f, const ImVec2 &align = ImVec2(0.5f, 0.5f));

void drawElidedText(ImDrawList *dl, const ImRect &rect, const std::string &text, ImU32 col, bool align_right = false);

float markerSize();
void drawColorMarker(ImDrawList *dl, const ImVec2 &pos, ImU32 col);

void loadFonts();
void applyTheme(int theme);
bool isDarkTheme();

ImU32 highlightedTextColor();
ImU32 paletteBrightText();


void setNextWindowFloatsOut();
#ifdef __APPLE__


void setMacAppName(const char *name);

bool isNativeFullScreen(GLFWwindow *window);
void toggleNativeFullScreen(GLFWwindow *window);
#endif


void setNextDialogWindow(const ImVec2 &size);

bool beginDialog(const char *id, PopupOwner *owner, const ImVec2 &size, ImGuiWindowFlags flags = ImGuiWindowFlags_NoResize);

const float TOOLBAR_ITEM_SPACING = 1.0f;
const float TOOLBAR_BUTTON_PADDING = 4.0f;
const float SLIDER_LENGTH = 13.0f;
const float SLIDER_THICKNESS = 13.0f;



struct ToolbarItem {
  float width;
  std::function<void()> draw;
  std::string menu_label;
  std::function<void()> trigger;
  bool enabled = true;
  bool in_menu = true;
};
void beginToolbar();
void endToolbar();
float toolbarButtonWidth(const std::string &label);

float toolbarWidth(const std::vector<ToolbarItem> &items, size_t spacer_index);

void drawToolbar(const std::vector<ToolbarItem> &items, size_t spacer_index);



float menuButtonWidth(const std::string &text, bool bold = false);
bool menuButton(const char *id, const std::string &text, const char *popup_id, bool bold = false, float width = 0.0f);


void drawSliderHandle(ImDrawList *p, const ImRect &r);


bool fusionSliderInt(const char *label, int *v, int min, int max, float width);

ImFont *boldFont();
ImFont *monoFont();
void pushMonoFont(float size = 0.0f);
void popMonoFont();
void pushBoldFont();
void popBoldFont();
void pushLargeFont();
void popLargeFont();
