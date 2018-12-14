#include <iostream>
#include <csignal>
#include <cstdlib>

#include "camio.hpp"

#include <opencv2/highgui.hpp>

bool received_sigint = false;

void signal_handler(int signal) {
  if(signal == SIGINT)
    received_sigint = true;
}


void version() {
  for(auto& v : camio::versions()) {
    std::cout << v << std::endl;
  }
}


void list() {
  auto devices = camio::enumerate();

  std::cout << "Found " << devices.size() << " device(s):" << std::endl;

  for(auto& cam : devices) {
    std::cout << " - " << cam.name << " (" << cam.id << ")"<< std::endl;
    std::cout << "   " << cam.description << std::endl;
  }
}


void track_expo(int value, void* ptr) {
  double exposure = 1 + 0.25 * value;
  ((camio::Camera*) ptr)->setExposure(exposure);
  std::cout << "exposure: " << exposure << " vs. " << ((camio::Camera*) ptr)->getExposure() << std::endl;
}

void track_rate(int value, void* ptr) {
  double framerate = value + 1.0;
  ((camio::Camera*) ptr)->setFrameRate(framerate);
  std::cout << "frame rate: " << framerate << " vs. " << ((camio::Camera*) ptr)->getFrameRate() << std::endl;
}

bool grab(int index) {
  auto devices = camio::enumerate();

  if(index >= devices.size()) {
    std::cerr << "Unknown device!" << std::endl;
    return false;
  }

  auto cam = camio::open(devices[index]);

  if(!cam) {
    std::cerr << "Failed to open device!" << std::endl;
    return false;
  }

  std::string window_name = devices[index].name;

  cam->setTrigger(camio::Camera::Timer);

  cam->setExposure(5.0);
  cam->setFrameRate(20);

  std::signal(SIGINT, signal_handler);

  cv::namedWindow(window_name);
  int expo = 4, rate = 19;
  cv::createTrackbar("expo", window_name, &expo, 40, track_expo, (void*) cam);
  cv::createTrackbar("rate", window_name, &rate, 20, track_rate, (void*) cam);

  cam->start();

  while(!received_sigint) {

      camio::Frame* frame = cam->grab();

      if(frame) {
        cv::Mat wrapped(frame->height, frame->width, CV_8UC1, frame->data);

        cv::imshow(window_name, wrapped);
        delete frame;
      }

      cv::waitKey(45);
  }

  cam->stop();
  delete cam;

  cv::destroyAllWindows();
  return true;
}


int main(int argc, char* argv[]) {
  // Parse arguments
  if(argc < 2) {
    std::cerr << argv[0] << " <version|list|grab>" <<  std::endl;
    return EXIT_FAILURE;
  }

  std::string cmd(argv[1]);

  // Initalize library
  camio::initializeAll();

  if(cmd == "version") {
    version();
  } else if(cmd == "list") {
    list();
  } else if(cmd == "grab") {
    if(argc != 3) {
      std::cerr << argv[0] << " grab <id>" <<  std::endl;
      return EXIT_FAILURE;
    }
    int index = atoi(argv[2]);
    if(!grab(index)) return EXIT_FAILURE;
  } else {
    std::cerr << "Unknown command: " << cmd << std::endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
