#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

#include "camio.hpp"

using namespace camio;

PYBIND11_MODULE(camio, m) {
  m.doc() = "MultiView Camera Input/Ouput Library";


  py::enum_<AdapterID>(m, "AdapterID")
    .value("DUMMY", AdapterID::DUMMY) 
    .value("PYLON", AdapterID::PYLON); 


  py::class_<CameraInfo>(m, "CameraInfo")
    .def_readwrite("id",          &CameraInfo::id)
    .def_readwrite("name",        &CameraInfo::name)
    .def_readwrite("description", &CameraInfo::description)
    .def("__repr__", [](const CameraInfo& info) {
      return "<camio.CameraInfo of '" + info.name + "' (" + info.id + ")>";
    });

  py::class_<CameraHandle, CameraInfo>(m, "CameraHandle")
    .def_readwrite("adapter", &CameraHandle::adapter);


  py::class_<Size>(m, "Size")
    .def(py::init<size_t, size_t>())
    .def("pixels", &Size::pixels, "Get number of pixels.")
    .def_readwrite("width",  &Size::width)
    .def_readwrite("height", &Size::height)
    .def("__repr__", [](const Size& size) {
      return "<camio.Size " + std::to_string(size.width) + " x " + std::to_string(size.height) + ">";
    });


  py::class_<Frame>(m, "Frame", py::buffer_protocol())
    .def(py::init<Size>())
    .def(py::init<size_t, size_t>())
    .def("at", &Frame::at, "Single pixel access.", py::arg("column"), py::arg("row"))
    .def("size", &Frame::size)
    .def_readonly("width",  &Frame::width)
    .def_readonly("height", &Frame::height)
    .def("data", [](Frame& f) {
      return py::array_t<uint8_t>(
        { f.height, f.width },
        { sizeof(uint8_t) * f.width, sizeof(uint8_t) },
        f.data);
    })
    .def_buffer([](Frame& f) -> py::buffer_info {
      return py::buffer_info(
        f.data,
        sizeof(uint8_t),
        py::format_descriptor<uint8_t>::format(),
        2,
        { f.height, f.width },
        { sizeof(uint8_t) * f.width, sizeof(uint8_t) });
    });


  py::enum_<Camera::TriggerMode>(m, "TriggerMode")
    .value("Software", Camera::Software)
    .value("Timer",    Camera::Timer)
    .value("External", Camera::External)
    .export_values();


  py::class_<Camera>(m, "Camera")
    .def_property("trigger",   &Camera::getTrigger,   &Camera::setTrigger)
    .def_property("framerate", &Camera::getFrameRate, &Camera::setFrameRate)
    .def_property("exposure",  &Camera::getExposure,  &Camera::setExposure)
    .def("resolution", &Camera::getFrameSize, "Get size of returned frame.")
    .def("start", &Camera::start, "Start camera.")
    .def("stop", &Camera::stop, "Stop camera.")
    .def("grab", &Camera::grab, "Grab next frame.");


  m.def("versions", &versions, "Return name of version of available adapters");


  m.def("initialize", &initialize, "Initialize a specific camera adapter.");

  m.def("initializeAll", &initializeAll, "Initialize all available camera adapters.");


  m.def("enumerate", &enumerate, "Return list of available cameras");


  m.def("open", py::overload_cast<AdapterID, std::string>(&open), "Open a camera");
  m.def("open", py::overload_cast<CameraHandle>(&open), "Open a camera");
}

