from flask import Flask, request, jsonify
import boto3
import base64
import uuid
import json

app = Flask(__name__)

# AWS Clients
s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')
BUCKET_NAME = 'animated-poster-generator-bucket'

@app.route('/generate', methods=['GET'])
def generate_poster():
    prompt = request.args.get('prompt', 'An epic fantasy movie poster')

    try:
        # Call Bedrock (Stable Diffusion)
        response = bedrock.invoke_model(
            modelId="stability.stable-diffusion-xl-v1",
            body=json.dumps({"text_prompts": [{"text": prompt}]}),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response['body'].read())
        image_bytes = base64.b64decode(result['artifacts'][0]['base64'])

        # Upload to S3
        file_name = f"{uuid.uuid4()}.png"
        s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=image_bytes, ContentType='image/png')

        # Generate pre-signed URL
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': file_name},
            ExpiresIn=3600
        )

        return jsonify({'url': presigned_url})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
