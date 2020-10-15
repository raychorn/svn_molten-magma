import unittest
suite = unittest.TestSuite()

import UpdateDict_test
UpdateDict_suite = UpdateDict_test.suite()
suite.addTest(UpdateDict_suite)

import RawSfdcConnection_test
RawSfdcConnection_suite = RawSfdcConnection_test.suite()
suite.addTest(RawSfdcConnection_suite)

import SfdcConnection_test
SfdcConnection_suite = SfdcConnection_test.suite()
suite.addTest(SfdcConnection_suite)

import Create_test
Create_suite = Create_test.suite()
suite.addTest(Create_suite)

import Retrieve_test
Retrieve_suite = Retrieve_test.suite()
suite.addTest(Retrieve_suite)

import Update_test
Update_suite = Update_test.suite()
suite.addTest(Update_suite)

unittest.TextTestRunner(verbosity=2).run(suite)
