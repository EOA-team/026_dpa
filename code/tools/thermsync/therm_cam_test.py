from flirpy.camera.tau import Tau

try:
    cam = Tau()
    print(f"✅ Camera detected")
    print(f"Available attributes: {[a for a in dir(cam) if not a.startswith('_')]}")
    cam.close()
except Exception as e:
    print(f"❌ Error: {e}")