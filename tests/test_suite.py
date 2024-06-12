import unittest
from test_user_config import TestUserConfig
from test_conversation_manager import TestConversationManager


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUserConfig))
    suite.addTest(unittest.makeSuite(TestConversationManager))
    # Add other test classes to the suite
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
