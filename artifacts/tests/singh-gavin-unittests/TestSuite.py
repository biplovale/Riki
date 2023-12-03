import unittest
from TestPageClass import TestPage  # Assuming WikiTest is the file name and also the class name
from TestWikiClass import WikiTest   # Assuming TestPage is the file name and also the class name

# Create a test loader
loader = unittest.TestLoader()

# Load tests from each test class
suite1 = loader.loadTestsFromTestCase(WikiTest)
suite2 = loader.loadTestsFromTestCase(TestPage)

# Combine the test suites
combined_suite = unittest.TestSuite([suite1, suite2])

# Run the combined test suite
runner = unittest.TextTestRunner(verbosity=2)
runner.run(combined_suite)
