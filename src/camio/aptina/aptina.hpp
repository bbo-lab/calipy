#pragma once

#include <apbase.h>

namespace aptina {
  std::string errorstring(int32_t error) {
    switch(error) {
    case MI_CAMERA_SUCCESS:
      return "CAMERA_SUCCESS";
    case MI_CAMERA_ERROR:
      return "CAMERA_ERROR";
    case AP_GRAB_FRAME_ERROR:
      return "GRAB_FRAME_ERROR";
    case AP_NOT_ENOUGH_DATA_ERROR:
      return "NOT_ENOUGH_DATA_ERROR";
    case AP_EOF_MARKER_ERROR:
      return "EOF_MARKER_ERROR";
    case AP_BUFFER_SIZE_ERROR:
      return "BUFFER_SIZE_ERROR";
    case AP_SENSOR_FILE_PARSE_ERROR:
      return "SENSOR_FILE_PARSE_ERROR";
    case AP_SENSOR_DOES_NOT_MATCH:
      return "SENSOR_DOES_NOT_MATCH";
    case AP_SENSOR_NOT_INITIALIZED:
      return "SENSOR_NOT_INITIALIZED";
    case AP_SENSOR_NOT_SUPPORTED:
      return "SENSOR_NOT_SUPPORTED ";
    case AP_I2C_BIT_ERROR:
      return "I2C_BIT_ERROR";
    case AP_I2C_NACK_ERROR:
      return "I2C_NACK_ERROR";
    case AP_I2C_TIMEOUT:
      return "I2C_TIMEOUT";
    case AP_CAMERA_TIMEOUT:
      return "CAMERA_TIMEOUT";
    case AP_TOO_MUCH_DATA_ERROR:
      return "TOO_MUCH_DATA_ERROR";
    case AP_CAMERA_NOT_SUPPORTED:
      return "CAMERA_NOT_SUPPORTED ";
    case AP_CRC_ERROR:
      return "CRC_ERROR";
    case AP_PARSE_SUCCESS:
      return "PARSE_SUCCESS";
    case AP_DUPLICATE_DESC_ERROR:
      return "DUPLICATE_DESC_ERROR";
    case AP_PARSE_FILE_ERROR:
      return "PARSE_FILE_ERROR";
    case AP_PARSE_REG_ERROR:
      return "PARSE_REG_ERROR";
    case AP_UKNOWN_SECTION_ERROR:
      return "UKNOWN_SECTION_ERROR";
    case AP_CHIP_DESC_ERROR:
      return "CHIP_DESC_ERROR";
    case AP_PARSE_ADDR_SPACE_ERROR:
      return "PARSE_ADDR_SPACE_ERROR";
    case AP_INI_SUCCESS:
      return "INI_SUCCESS";
    case AP_INI_KEY_NOT_SUPPORTED:
      return "INI_KEY_NOT_SUPPORTED";
    case AP_INI_LOAD_ERROR:
      return "INI_LOAD_ERROR";
    case AP_INI_POLLREG_TIMEOUT:
      return "INI_POLLREG_TIMEOUT";
    case AP_INI_HANDLED_SUCCESS:
      return "INI_HANDLED_SUCCESS";
    case AP_INI_HANDLED_ERROR:
      return "INI_HANDLED_ERROR";
    case AP_INI_NOT_HANDLED:
      return "INI_NOT_HANDLE";
    default:
      return "unknown error " + std::to_string(error);
    }
  }

  std::string effectstring(int32_t effect) {
    switch(effect) {
    case AP_FLAG_OK:
      return "No side-effect";
    case AP_FLAG_REALLOC:
      return "Image buffer size may change";
    case AP_FLAG_PAUSE:
      return "Sensor may stop streaming";
    case AP_FLAG_RESUME:
      return "Sensor may resume streaming";
    case AP_FLAG_NOT_SUPPORTED:
      return "Selecting a mode that is not supported by the demo system";
    case AP_FLAG_ILLEGAL_REG_COMBO:
      return "The new value creates an invalid combination with some other register(s)";
    case AP_FLAG_ILLEGAL_REG_VALUE:
      return "The new value is not supported by the device";
    case AP_FLAG_REGISTER_RESET:
      return "Many other register values will change (reset or state change)";
    case AP_FLAG_CLOCK_FREQUENCY:
      return "The clock frequency will change (this is a PLL register or clock divider)";
    case AP_FLAG_REG_LIST_CHANGED:
      return "The set of camera registers will change";
    case AP_FLAG_NOT_ACCESSIBLE:
      return "Register is not accessible (standby)";
    case AP_FLAG_READONLY:
      return "Writing a read-only register";
    case AP_FLAG_WRITEONLY:
      return "Reading a write-only register";
    case AP_FLAG_OUTSIDE_REG_MASK:
      return "Writing outside the register mask (setting undefined bits)";
    case AP_FLAG_H264_RESTART:
      return "Restart H.264 decoding (or similar)";
    case AP_FLAG_USERCANCEL:
      return "User cancelled register write";
    default:
      return "unknown effect " + std::to_string(effect);
    }
  }


  std::string lasterrorstring() {
    return errorstring(ap_GetLastError());
  }

}
