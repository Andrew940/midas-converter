#!/usr/bin/env python3
import sys
import os
from argparse import ArgumentParser
import cv2
import numpy as np
import logging as log
from openvino.inference_engine import IECore
import matplotlib.pyplot as plt
import glob

def main():
    # arguments
    parser = ArgumentParser()

    parser.add_argument(
        "-m", "--model", help="Required. Path to an .xml file with a trained model", required=True, type=str)
    parser.add_argument(
        "-i", "--input", help="Required. Path to the folder containing the image files", required=True, type=str)
    parser.add_argument("-l", "--cpu_extension",
        help="Optional. Required for CPU custom layers. Absolute MKLDNN (CPU)-targeted custom layers. "
        "Absolute path to a shared library with the kernels implementations", type=str, default=None)
    parser.add_argument("-d", "--device",
        help="Optional. Specify the target device to infer on; CPU, GPU, FPGA, HDDL or MYRIAD is acceptable. "
        "Sample will look for a suitable plugin for device specified. Default value is CPU", default="CPU", type=str)
    parser.add_argument("-c", "--colormap",
        help="Optional. Specify the colormap for the depth output. Default value is inferno", default="inferno", type=str)

    args = parser.parse_args()

    # logging
    log.basicConfig(format="[ %(levelname)s ] %(message)s",
                    level=log.INFO, stream=sys.stdout)

    log.info("creating inference engine")
    ie = IECore()
    if args.cpu_extension and "CPU" in args.device:
        ie.add_extension(args.cpu_extension, "CPU")

    log.info("Loading network")
    net = ie.read_network(args.model, os.path.splitext(args.model)[0] + ".bin")

    assert len(net.input_info) == 1, "Sample supports only single input topologies"
    assert len(net.outputs) == 1, "Sample supports only single output topologies"

    log.info("preparing input blobs")
    input_blob = next(iter(net.input_info))
    out_blob = next(iter(net.outputs))
    net.batch_size = 1

    # loading model to the plugin
    log.info("loading model to the plugin")
    exec_net = ie.load_network(network=net, device_name=args.device)

    files = [f for f in glob.glob(args.input + "/*.png", recursive=False)]

    print("start converting...")

    for i, file in enumerate(files):
        print("[%d/%d] converting %s..." % (i+1, len(files), file))
        name = os.path.splitext(file)[0]

        # read and pre-process input image
        _, _, height, width = net.input_info[input_blob].input_data.shape

        image = cv2.imread(file, cv2.IMREAD_COLOR)
        (input_height, input_width) = image.shape[:-1]

        # resize
        if (input_height, input_width) != (height, width):
            image = cv2.resize(image, (width, height), cv2.INTER_CUBIC)

        # prepare input
        image = image.astype(np.float32)
        image = image.transpose((2, 0, 1))
        image_input = np.expand_dims(image, 0)

        # start sync inference
        res = exec_net.infer(inputs={input_blob: image_input})

        # processing output blob
        disp = res[out_blob][0]

        # resize disp to input resolution
        disp = cv2.resize(disp, (input_width, input_height), cv2.INTER_CUBIC)

        # rescale disp
        disp_min = disp.min()
        disp_max = disp.max()

        if disp_max - disp_min > 1e-6:
            disp = (disp - disp_min) / (disp_max - disp_min)
        else:
            disp.fill(0.5)
        # png
        out = '%s_disp.png' % name
        plt.imsave(out, disp, vmin=0, vmax=1, cmap=args.colormap)

    print("done!")


if __name__ == '__main__':
    main()
