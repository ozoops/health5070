
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import numpy as np
from PIL import Image

# Add the backend directory to the system path to allow module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now, import the class to be tested
# We need to set a dummy key *before* the module is imported if it's used at the module level
os.environ['OPENAI_API_KEY'] = 'test_key'
from video import VideoProducer

class TestVideoProducer(unittest.TestCase):

    def setUp(self):
        """Set up a test environment for each test case."""
        # Ensure the video directory exists
        if not os.path.exists('generated_videos'):
            os.makedirs('generated_videos')
        
        # Patch os.environ to ensure a consistent API key for all tests
        self.env_patcher = patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
        self.env_patcher.start()

        self.producer = VideoProducer()

    def tearDown(self):
        """Clean up after each test case."""
        self.env_patcher.stop()

    def test_initialization(self):
        """Test that the VideoProducer initializes correctly."""
        self.assertIsNotNone(self.producer.client)
        self.assertEqual(self.producer.api_key, 'test_key')

    @patch.dict(os.environ, {'OPENAI_API_KEY': ''})
    def test_init_raises_error_if_api_key_missing(self):
        """Test that ValueError is raised if the OpenAI API key is missing."""
        with self.assertRaises(ValueError):
            VideoProducer()

    @patch('requests.get')
    @patch('openai.resources.images.Images.generate')
    def test_generate_ai_image_success(self, mock_generate, mock_requests_get):
        """Test successful AI image generation."""
        # Mock the OpenAI API response
        mock_image_url = "http://fake-url.com/image.png"
        mock_generate.return_value = MagicMock(data=[MagicMock(url=mock_image_url)])

        # Mock the requests.get call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake_image_data'
        mock_requests_get.return_value = mock_response

        # Use mock_open to simulate file writing
        m = mock_open()
        with patch('builtins.open', m):
            result = self.producer.generate_ai_image("A test prompt", "dummy_path.png")
            
            # Assertions
            self.assertTrue(result)
            mock_generate.assert_called_once()
            mock_requests_get.assert_called_once_with(mock_image_url, timeout=60)
            m.assert_called_once_with("dummy_path.png", "wb")
            m().write.assert_called_once_with(b'fake_image_data')

    @patch('openai.resources.images.Images.generate')
    def test_generate_ai_image_failure(self, mock_generate):
        """Test AI image generation failure after retries."""
        # Mock the OpenAI API to raise an exception
        mock_generate.side_effect = Exception("API Error")

        with patch('time.sleep') as mock_sleep:
            result = self.producer.generate_ai_image("A test prompt", "dummy_path.png")
            
            # Assertions
            self.assertFalse(result)
            self.assertEqual(mock_generate.call_count, 3) # Should retry 3 times
            self.assertEqual(mock_sleep.call_count, 3)

    @patch('video.VideoProducer.generate_ai_image')
    def test_generate_scene_image_fallback(self, mock_generate_ai_image):
        """Test the fallback mechanism in generate_scene_image."""
        # Simulate failure of AI image generation
        mock_generate_ai_image.return_value = False

        # Mock PIL to avoid actual image creation
        with patch('PIL.Image.new') as mock_pil_new:
            mock_image = MagicMock()
            mock_pil_new.return_value = mock_image

            fallback_path = self.producer.generate_scene_image("test sentence", "test_id", 1)
            
            # Assertions
            self.assertTrue(fallback_path.startswith(os.path.join('generated_videos', 'scene_fallback_')))
            mock_pil_new.assert_called_once()
            mock_image.save.assert_called_once()

    def test_render_caption_image(self):
        """Test that caption rendering produces a valid numpy array."""
        # This test checks if the function runs without errors and returns the correct type/shape
        with patch('video.VideoProducer.get_font_path', return_value=None): # Use default font
            caption_array = self.producer.render_caption_image("Hello, world!")
            
            # Assertions
            self.assertIsInstance(caption_array, np.ndarray)
            self.assertEqual(caption_array.shape, (self.producer.H, self.producer.W, 4))

    @patch('openai.resources.chat.completions.Completions.create')
    def test_generate_intro_sentence_success(self, mock_create):
        """Test successful intro sentence generation."""
        expected_intro = "This is a generated intro."
        mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content=expected_intro))])
        
        result = self.producer._generate_intro_sentence("A test title")
        
        self.assertEqual(result, expected_intro)
        mock_create.assert_called_once()

    @patch('openai.resources.chat.completions.Completions.create')
    def test_generate_intro_sentence_failure(self, mock_create):
        """Test fallback behavior when intro generation fails."""
        mock_create.side_effect = Exception("API Error")
        
        title = "A test title"
        result = self.producer._generate_intro_sentence(title)
        
        self.assertEqual(result, title) # Should return the original title

    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=1024)
    @patch('video.gTTS')
    @patch('video.mp.ImageClip')
    @patch('video.mp.AudioFileClip')
    @patch('video.mp.CompositeVideoClip')
    @patch('video.mp.concatenate_videoclips')
    @patch('video.mp.concatenate_audioclips')
    @patch('video.VideoProducer._generate_intro_sentence')
    @patch('video.VideoProducer.generate_scene_image')
    @patch('video.VideoProducer.render_caption_image')
    @patch('video.VideoProducer.ken_burns')
    def test_create_video_file_logic(self, mock_ken_burns, mock_render_caption, mock_gen_scene_img, mock_gen_intro, 
                                     mock_concat_audio, mock_concat_video, mock_composite, 
                                     mock_audio_clip, mock_image_clip, mock_gtts, mock_getsize, mock_exists):
        """Test the main logic of the video creation pipeline by mocking dependencies."""
        # Setup mocks
        mock_gen_intro.return_value = "Test intro"
        mock_gen_scene_img.return_value = "path/to/fake_image.png"
        mock_audio_clip.return_value = MagicMock(duration=3)
        mock_ken_burns.return_value = MagicMock()
        mock_render_caption.return_value = np.zeros((self.producer.H, self.producer.W, 4))
        
        # Mock the final video object and the chained calls to it
        final_video_mock = MagicMock()
        mock_concat_video.return_value.set_audio.return_value.fx.return_value = final_video_mock
        
        script = "This is the first sentence. And this is the second."
        
        # Execute
        video_path = self.producer.create_video_file("test_article", "Test Title", script)
        
        # Assertions
        self.assertIn("video_test_article", video_path)
        self.assertTrue(video_path.endswith(".mp4"))
        
        # Check that key functions were called
        self.assertEqual(mock_gen_intro.call_count, 1)
        self.assertEqual(mock_gtts.call_count, 3) # 1 for intro + 2 for sentences
        self.assertEqual(mock_gen_scene_img.call_count, 3) # 1 for intro + 2 for sentences
        
        # Check that the final video file was written
        final_video_mock.write_videofile.assert_called_once()

if __name__ == '__main__':
    unittest.main()
