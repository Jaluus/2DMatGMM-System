# Installation Guide

Welcome to our detailed Installation Guide. In the following sections, we will assist you in installing the requisite software and setup procedures to seamlessly integrate our system with your laboratory equipment.

## Prerequisites

Before proceeding, please ensure you have Python installed on your machine. This software is needed to run the following steps.
If you need detailed steps to install python on your system please refer to the installation guide in the [2DMatGMM Repository](https://github.com/jaluus/2DMatGMM).

## Software Installation

To install the necessary Python packages for our system, please execute the following command in your terminal:

```shell
pip install -r requirements.txt
```

Please note that this command should be executed from the directory where `requirements.txt` is located.

## Hardware Setup

### Microscope Setup

To prepare your microscope for integration, please install the [NIS-Elements Basic Research](https://www.microscope.healthcare.nikon.com/products/software/nis-elements/nis-elements-basic-research) software from Nikon. This will install the necessary drivers required for all microscope modules.

### Tango Desktop 2 Setup

For Tango Desktop 2, please download the DLL files available on their [official website](https://www.marzhauser.com/nc/en/service/downloads.html?tx_abdownloads_pi1%5Bcategory_uid%5D=184&tx_abdownloads_pi1%5Bcid%5D=365&cHash=09d7e72f47fce9825f477ac230e512b2).

After downloading, extract the folder containing the DLL files. Then, copy the `DLL_Files` folder into the `Drivers/Motor_Driver` folder.

```shell
Drivers
├── Interfaces
│   └── ...
└── Motor_Driver
    ├── DLL_Files
    │   ├── TangoDLL_32Bit_VXXXX
    │   └── TangoDLL_64Bit_VXXXX
    ├── motor_class.py
    └── ...
```

### Camera Setup

For the camera integration, no additional steps are required. The necessary drivers should already be included in the repository.

## Custom Hardware Integration

If you wish to use hardware other than those listed above, you can create custom drivers by adhering to the interfaces provided in the `Drivers/Interfaces` folder.

These interfaces outline the functions required to ensure compatibility with our system. You can implement these interfaces using any hardware-specific logic, as long as the resultant functions are consistent with the descriptions provided.
