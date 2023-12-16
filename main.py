import cv2
import mediapipe as mp
import time
import pyaudio
import wave

###################################################################################################################
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode
result_name = [None,0]
def hand_detector(frame,holistic):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = holistic.process(frame_rgb)
    ## for drawing left hand
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                                  mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=4),
                                  mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2))   
    ## From drawing right hand
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                                  mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=4),
                                  mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2))
            
    return frame
def print_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
     #print('gesture recognition result: {}'.format(result))
     if len(result.gestures) and len(result.gestures[0]):
      gesture = result.gestures[0][0]
      if result_name[0] != gesture.category_name:
         result_name[0] = gesture.category_name
         result_name[1] = 0
      else:
         result_name[1] += 1
      print(gesture.category_name,result_name[1])
        
     else:
        result_name[0] = None
        result_name[1] = 0
    
options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path='new.task'),
    running_mode=VisionRunningMode.LIVE_STREAM,result_callback=print_result)
recognizer =  GestureRecognizer.create_from_options(options) 
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
holistic = mp_holistic.Holistic(min_detection_confidence=0.7, min_tracking_confidence=0.8)
##########################################################################################################
def resize_and_paste(image, target_image):
    # Resize the image
    width,height = 100,100
    resized_image = cv2.resize(image, (width, height))

    # Get the dimensions of the resized image
    img_height, img_width, _ = resized_image.shape

    # Paste the resized image at the top left corner of the target image
    target_image[0:img_height, 0:img_width] = resized_image

    return target_image

def play_video(video,audio):
    # Open the video file
    index = 0
    lenght = 3
    flag = True
    timestamp = 0
    while flag:
        video_path = video[index]
        cap = cv2.VideoCapture(video_path)
        cap2 = cv2.VideoCapture(0)
        # Initialize video playback status
        paused = False
        player = WithPyAudio(audio[index])
        start_time = time.time()
        while True:
            ret,frame = cap.read()
            ret1,frame1 = cap2.read()
            timestamp += 1
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame1)
            recognition_result = recognizer.recognize_async(mp_image,timestamp)
            if not ret:
                break
            frame1 = hand_detector(frame1,holistic)
            frame2 = resize_and_paste(frame1,frame)
            # Display the frame in a window
            cv2.imshow('Video Player', frame2)
            elapsed = (time.time() - start_time) * 1000  # msec
            play_time = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            sleep = max(1, int(play_time - elapsed))

            # Check for key press
            key = cv2.waitKey(1)

            # Exit if 'q' key is pressed
            if key == ord('q') or result_name[0] == "four" and result_name[1] > 5:
                flag = False
                break

            # Pause/play video if 'p' key is pressed
            if key == ord('n') or result_name[0] == "two" and result_name[1] > 5:        
                print('hello')
                paused = not paused
                time.sleep(0.7)
                result_name[1] = 0

            # Next frame if 'n' key is pressed
            if key == ord('m') or result_name[0] ==  "three" and result_name[1] > 5:
                index += 1
                index = index % lenght
                video_path = video[index]
                cap = cv2.VideoCapture(video_path)
                print(index)
                time.sleep(0.7)
                player = WithPyAudio(audio[index])
                start_time = time.time()
                result_name[1] = 0
                


            # Previous frame if 'b' key is pressed
            if key == ord('b') or result_name[0] ==  "one" and result_name[1] > 5:
                index -= 1
                index = index % lenght
                video_path = video[index]
                cap = cv2.VideoCapture(video_path)
                print(index)
                time.sleep(0.7)
                player = WithPyAudio(audio[index])
                start_time = time.time()
                result_name[1] = 0

            if key == ord('u') or result_name[0] ==  "ok" and result_name[1] > 5:
                print('Here')
                player.increase_volume(0.1)
            if key == ord('d') or result_name[0] ==  "fist" and result_name[1] > 5:
                print('Here')
                player.decrease_volume(0.1)

        # Release the video file
        cap.release()
        cv2.destroyAllWindows()


                

class WithPyAudio:
    def __init__(self, audio_file):
        self.wf = wave.open(audio_file, "rb")
        self.p = pyaudio.PyAudio()

        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.wf.getsampwidth()),
            channels=self.wf.getnchannels(),
            rate=self.wf.getframerate(),
            output=True,
            stream_callback=self._stream_cb,
        )
        
        self.volume = 1.0  # Initialize volume to max (1.0)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.wf.close()

    def _stream_cb(self, in_data, frame_count, time_info, status):
        data = self.wf.readframes(frame_count)
        data = self._adjust_volume(data)  # Adjust volume
        return (data, pyaudio.paContinue)

    def _adjust_volume(self, data):
        audio_data = bytearray(data)
        for i in range(0, len(audio_data), 2):
            sample = int.from_bytes(audio_data[i:i+2], byteorder='little', signed=True)
            sample = int(sample * self.volume)
            sample = min(max(sample, -32768), 32767)  # Clamp the sample value
            audio_data[i:i+2] = sample.to_bytes(2, byteorder='little', signed=True)
        return bytes(audio_data)

    def increase_volume(self, increment):
        self.volume = min(self.volume + increment, 1.0)

    def decrease_volume(self, decrement):
        self.volume = max(self.volume - decrement, 0.0)


video  = ['samples/sample1.mp4','samples/sample2.mp4','samples/sample3.mp4']
audio  = ['samples/sample1.wav','samples/sample2.wav','samples/sample3.wav']
play_video(video,audio)
# Close all OpenCV windows
cv2.destroyAllWindows()