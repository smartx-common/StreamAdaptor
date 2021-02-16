
echo "start recording..."
nohup python3.8 StreamAdaptor.py \
    --write_video ./Output/front-"$(date +%Y-%m-%d-%H-%M-%S)".avi \
    --limit_time 1800 \
    --input_video_path rtsp://221.163.251.6/stream1 &

nohup python3.8 StreamAdaptor.py \
    --write_video ./Output/front-"$(date +%Y-%m-%d-%H-%M-%S)".avi \
    --limit_time 1800 \
    --input_video_path rtsp://221.163.251.8/stream1 &

