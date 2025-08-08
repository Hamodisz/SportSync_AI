from content_studio.ai_video.video_composer import compose_video_from_assets
from agents.marketing.video_pipeline.image_generator import generate_images
from agents.marketing.video_pipeline.voice_generator import generate_voiceover  # أو generate_voice_from_script
from agents.marketing.video_pipeline.script_writer import generate_script_from_traits

class VideoFactory:
    def _init_(self, image_duration=4, resolution=(1080,1080)):
        self.image_duration = image_duration
        self.resolution = resolution

    def produce_from_traits(self, user_data: dict, lang="ar") -> str | None:
        script = generate_script_from_traits(user_data, lang)
        generate_images(script, lang)
        # لو تستخدم gTTS:
        try:
            generate_voiceover(script, lang)
        except TypeError:
            from content_studio.ai_voice.voice_generator import generate_voice_from_script
            generate_voice_from_script(script, lang)
        return compose_video_from_assets(image_duration=self.image_duration, resolution=self.resolution)

    def produce_from_script(self, script: str, lang="ar") -> str | None:
        generate_images(script, lang)
        try:
            generate_voiceover(script, lang)
        except TypeError:
            from content_studio.ai_voice.voice_generator import generate_voice_from_script
            generate_voice_from_script(script, lang)
        return compose_video_from_assets(image_duration=self.image_duration, resolution=self.resolution)
