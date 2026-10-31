import unittest
from unittest.mock import MagicMock, patch
from extract import JobPosting, extract_job
class TestExtractJob(unittest.TestCase):
    @patch("extract.time.sleep")                                                        
    @patch("extract.client.models.generate_content") 
    def test_retry_on_failure_then_succeed(self, mock_generate, mock_sleep):
        mock_success = MagicMock()                                                              
        mock_success.parsed = JobPosting(                                                       
            title="Software Engineer",                                                          
            company="Acme Corp",                                                                
            skills=["Python"])
        mock_generate.side_effect = [Exception("503 High Demand"), mock_success]
        result = extract_job("Dummy job posting text")
        self.assertEqual(result.title, "Software Engineer")
        self.assertEqual(mock_generate.call_count, 2) 
if __name__ == "__main__":                                                              
        unittest.main()    
         

