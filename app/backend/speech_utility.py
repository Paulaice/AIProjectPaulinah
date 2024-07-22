import requests, uuid
import azure.cognitiveservices.speech as speechsdk
import io

from azure.storage.blob import (
    BlobServiceClient
)


def text_to_text(text, recognized_lang, target_lang):

    # Add your key and endpoint
    key = "4cd83c61ef614a0b8ea597c01959de7f"
    endpoint = "https://api.cognitive.microsofttranslator.com"

    # location, also known as region.
    # required if you're using a multi-service or regional (not global) resource. It can be found in the Azure portal on the Keys and Endpoint page.
    location = "eastus"

    path = '/translate'
    constructed_url = endpoint + path

    params = {
        'api-version': '3.0',
        'from': recognized_lang,
        'to': [target_lang]
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        # location required if you're using a multi-service or regional (not global) resource.
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # You can pass more than one object in body.
    body = [{
        'text': text
    }]

    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()

    return response[0]['translations'][0]['text']

def blob_to_speech_to_text_text(blob):
    
    
    blob_name=blob
    # Configuration details
    container_name = "test-audio"
    #blob_name = "input_output.wav"
    connection_string = "DefaultEndpointsProtocol=https;AccountName=infoasststoreibocv;AccountKey=bckyxCySDrywT0ssHyEVUO1bKYoa96uVrHuUgxYPpRIu0CvtxEipK1poIm8f+xi5f6+IZGfqI78N+ASt4u1ymw==;EndpointSuffix=core.windows.net"
    speech_key = "e9089af9e0fa4e87b82bccb9d7f6bf87"
    service_region = "eastus"
    target_language="en"
    
    # Create a BlobServiceClient and download the audio blob into memory
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    download_stream = io.BytesIO()
    blob_client.download_blob().readinto(download_stream)
    download_stream.seek(0)  # Reset the stream position


    # Use the downloaded stream with PushAudioInputStream
    push_stream = speechsdk.audio.PushAudioInputStream()
    push_stream.write(download_stream.read())
    push_stream.close()
    
    # Configure speech recognition
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["hi-IN","en-US","zu-ZA"])

    # Configure the audio input from the file
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

    # Create the speech recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, auto_detect_source_language_config=auto_detect_source_language_config, audio_config=audio_config)

    print("Processing the audio file for speech recognition...")
    result = speech_recognizer.recognize_once()

    # Process the result
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        detected_language = speechsdk.AutoDetectSourceLanguageResult(result).language
        print(f"Recognized: {result.text} in language {detected_language}")
        translated_english_text = text_to_text(result.text, detected_language, 'en')
        # return result.text, detected_language
        print("detected_language: ", detected_language)
        return translated_english_text,detected_language
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized")
    elif result.reason == speechsdk.ResultReason.Canceled:
        print(f"Speech Recognition canceled: {result.cancellation_details.reason}")
        if result.cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {result.cancellation_details.error_details}")
    return None, None


def text_to_text_to_speech_to_blob(output_blob_name,output_english_text,target_language):
    translated_target_text=text_to_text(output_english_text,"en",target_language)
    container_name = "test-audio"
    connection_string = "DefaultEndpointsProtocol=https;AccountName=infoasststoreibocv;AccountKey=bckyxCySDrywT0ssHyEVUO1bKYoa96uVrHuUgxYPpRIu0CvtxEipK1poIm8f+xi5f6+IZGfqI78N+ASt4u1ymw==;EndpointSuffix=core.windows.net"
    speech_key = "e9089af9e0fa4e87b82bccb9d7f6bf87"
    service_region = "eastus"
    # Initialize the Azure Speech service configuration
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    file_config = speechsdk.audio.AudioOutputConfig(filename=output_blob_name)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)
    

    # Synthesize the text and get the result
    result = synthesizer.speak_text_async(translated_target_text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        # Create a BlobServiceClient using the connection string
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=output_blob_name)

        # Upload the audio data directly to the blob
        blob_client.upload_blob(io.BytesIO(result.audio_data), overwrite=True)
        print(f'Audio uploaded to blob storage: {output_blob_name}')
    else:
        print(f'Text-to-speech conversion failed: {result.reason}')
    return output_blob_name











