import unittest 

from app import *

"""
This is a class for testing the methods that are required:
    
    -Some of the asserts can be changed depending on the type 
    of the data structure.
    
    However, the values that are tested are CONSTANT.
    
    E.g. self.assertTrue(len(result)==19)
    
    
"""

class AppTest(unittest.TestCase): 
    def setUp(self): 
        print ("Setup")
    #Helper functions
    def test_is_valid_method(self):
        self.assertFalse(is_valid_method(None))
        self.assertFalse(is_valid_method(""))
        self.assertTrue(is_valid_method("get"))
        self.assertTrue(is_valid_method("GET"))
        self.assertFalse(is_valid_method("Other"))
    
    def test_is_valid_status(self):
        self.assertFalse(is_valid_status(None))
        self.assertFalse(is_valid_status(""))
        self.assertFalse(is_valid_status("303"))
        self.assertTrue(is_valid_status("200"))
        self.assertTrue(is_valid_status("206"))

    def test_is_valid_resource(self):
        self.assertFalse(is_valid_resource(None))
        self.assertFalse(is_valid_resource(""))
        self.assertFalse(is_valid_resource("file.mp4"))
        self.assertTrue(is_valid_resource("file.mp3"))
        self.assertTrue(is_valid_resource("file.MP3"))
        
    def test_is_valid_user_agent(self):
        self.assertFalse(is_valid_user_agent(None))
        self.assertFalse(is_valid_user_agent(""))
        self.assertFalse(is_valid_user_agent("Bot"))
        self.assertFalse(is_valid_user_agent("Spider"))
        self.assertFalse(is_valid_user_agent("Crawler"))
        self.assertFalse(is_valid_user_agent("Heritrix"))
        self.assertTrue(is_valid_user_agent("Mozilla Firefox"))
        
    #Functions
    def test_load_dataset(self):
        result = load_dataset("toy_data.csv")
        self.assertTrue(len(result)==19)
   
    def test_analyze_dataset(self):
        data_entries = load_dataset("toy_data.csv")
        observations = analyze_dataset(data_entries)
        self.assertTrue(len(observations)==17)
    
    def test_generate_stats(self):
        data_entries = load_dataset("toy_data.csv")
        observations = analyze_dataset(data_entries)
        stats = generate_stats(observations)
        
        self.assertTrue(stats["Download 200"]==0)
        self.assertTrue(stats["Download 206"]==12)
        self.assertTrue(stats["Bad status"]==0)
        self.assertTrue(stats["Bad method"]==5)
        self.assertTrue(stats["Bad format resource"]==0)
        self.assertTrue(stats["Bot detected"]==0)
      
    def test_list_top_k_programs(self):
        data_entries = load_dataset("toy_data.csv")
        observations = analyze_dataset(data_entries)
        k = 0
        all_top_programs = list_top_programs(observations)
        top_k = list_top_k_programs(all_top_programs, k)
        self.assertTrue(len(top_k)==0)
        k = 3
        top_k = list_top_k_programs(all_top_programs, k)
        self.assertTrue(len(top_k)==3)
        #Check the values of each program
        self.assertTrue(top_k[0][1]==2)
        self.assertTrue(top_k[1][1]==2)
        self.assertTrue(top_k[2][1]==2)
    
    def test_recommend(self):
        data_entries = load_dataset("toy_data.csv")
        observations = analyze_dataset(data_entries)
        episode_set = list_episodes(observations)
        user="df273cf4-d335-4b7f-b979-17212e8b84d3"
        recommendations = recommend(observations, episode_set, user) 
        self.assertTrue(len(recommendations)==0)
  
        
if __name__ == '__main__': 
    unittest.main()    