import os
import streamlit as st
import google.generativeai as genai
import assemblyai as aai
from streamlit.components.v1 import html

# Set your API keys
google_api_key = 'AIzaSyDENmkR2zOJDCdqG1roGaEznmCwLgiS6Uc'
assemblyai_api_key = '458d04f86c934454bb8148b4f595a171'
os.environ['GOOGLE_API_KEY'] = google_api_key
aai.settings.api_key = assemblyai_api_key

# Configure the Google Generative AI API
genai.configure(api_key=google_api_key)

# Function to generate follow-up question
def generate_followup_question(response):
    prompt = f"Ask a follow-up question based on this answer:\n\n'{response}'"
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text.strip()

# Function to transcribe the video using AssemblyAI
def transcribe_video(video_path):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(video_path)
    return transcript.text

# Streamlit app begins here
st.title("Dynamic Interview Questioning System")

# Initialize session state if not already initialized
if 'question_flow' not in st.session_state:
    st.session_state['question_flow'] = [{"question": "Tell me about yourself", "answer": "", "transcribed": False}]
if 'responses' not in st.session_state:
    st.session_state['responses'] = []
if 'processing_video' not in st.session_state:
    st.session_state['processing_video'] = False
if 'uploaded_videos' not in st.session_state:
    st.session_state['uploaded_videos'] = [None] * 5  # To store the uploaded videos for 5 questions

# Display the current question
current_question_index = len(st.session_state['question_flow']) - 1
current_question = st.session_state['question_flow'][current_question_index]["question"]
st.write(f"Q{current_question_index + 1}: {current_question}")

# Video recording component
html("""
    <div style="text-align: center;">
        <video id="video_answer" width="320" height="240" controls></video>
        <br>
        <button id="start_recording">Start Recording</button>
        <button id="stop_recording" disabled>Stop Recording</button>
        <button id="upload_video" disabled>Upload Video</button>
        <br><br>
        <input type="file" id="file_input" accept="video/mp4" style="display: none;" />
    </div>
    <script>
        let startButton = document.getElementById('start_recording');
        let stopButton = document.getElementById('stop_recording');
        let uploadButton = document.getElementById('upload_video');
        let video = document.getElementById('video_answer');
        let mediaRecorder;
        let recordedChunks = [];

        startButton.onclick = async () => {
            let stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            video.srcObject = stream;
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            recordedChunks = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                let blob = new Blob(recordedChunks, { type: 'video/mp4' });
                let url = URL.createObjectURL(blob);
                uploadButton.disabled = false;
                uploadButton.onclick = () => {
                    let a = document.createElement('a');
                    a.href = url;
                    a.download = 'video_answer.mp4';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                };
            };

            stopButton.disabled = false;
            startButton.disabled = true;
        };

        stopButton.onclick = () => {
            mediaRecorder.stop();
            video.srcObject.getTracks().forEach(track => track.stop());
            startButton.disabled = false;
            stopButton.disabled = true;
        };
    </script>
""", height=400)

# Upload video file
video_file = st.file_uploader(f"Upload your video answer for Question {current_question_index + 1}", type=["mp4"], key=f"video_{current_question_index}")

# Process video only if a new video is uploaded
if video_file and not st.session_state['processing_video'] and not st.session_state['question_flow'][current_question_index]["transcribed"]:
    st.session_state['processing_video'] = True  # Flag to prevent re-triggering the video processing

    with st.spinner("Transcribing video..."):
        # Save the uploaded video to a unique path
        video_path = f"uploaded_video_q{current_question_index + 1}.mp4"
        with open(video_path, "wb") as f:
            f.write(video_file.read())

        # Transcribe the video
        transcript = transcribe_video(video_path)

        # Update the answer in the current question flow
        st.session_state['question_flow'][current_question_index]["answer"] = transcript
        st.session_state['question_flow'][current_question_index]["transcribed"] = True
        
        # Display the transcription immediately
        st.write(f"Transcription: {transcript}")

        # Store the response
        st.session_state['responses'].append(transcript)

        # Automatically generate the next follow-up question
        followup_question = generate_followup_question(transcript)
        st.session_state['question_flow'].append({"question": followup_question, "answer": "", "transcribed": False})

        # Allow the app to update without causing infinite loop
        st.session_state['processing_video'] = False
        
        # Automatically display the next question without rerun loop
        st.experimental_rerun()  # Re-run the script to update the display

# Display the updated question and answer flow
st.subheader("Interview Progress")
for i, q in enumerate(st.session_state['question_flow']):
    st.write(f"Q{i+1}: {q['question']}")
    if q['transcribed']:
        st.write(f"A{i+1}: {q['answer']}")

# End interview after 5 questions
if len(st.session_state['question_flow']) == 6:
    st.subheader("Interview Complete")
    st.write("You have answered 5 questions. Thank you for completing the interview!")
