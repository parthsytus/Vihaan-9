from potassium import Potassium, Request, Response
from diffusers import StableDiffusionPipeline
import torch
import base64
from io import BytesIO

app = Potassium("image_gen_backend")

# @app.init runs at startup to load the model into the GPU
@app.init
def init():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = "runwayml/stable-diffusion-v1-5"
    
    # Load the pipeline
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id, 
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    pipe.to(device)
    
    return {
        "model": pipe
    }

# @app.handler runs for every API call
@app.handler()
def handler(context: dict, request: Request) -> Response:
    prompt = request.json.get("prompt")
    if not prompt:
        return Response(json={"error": "No prompt provided"}, status=400)

    model = context.get("model")
    
    # Generate the image
    # Note: we use a low step count (20) for faster generation
    image = model(prompt, num_inference_steps=20).images[0]
    
    # Convert image to Base64 string to send back over JSON
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return Response(
        json={"output": img_str}, 
        status=200
    )

if __name__ == "__main__":
    app.serve()