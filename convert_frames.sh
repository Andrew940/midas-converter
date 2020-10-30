#/bin/bash

# setup vars of open vino
[ -z "$INTEL_OPENVINO_DIR" ] && source "/opt/intel/openvino/bin/setupvars.sh"

python monodepth_convert.py -m public/midasnet/FP32/midasnet.xml -i frames