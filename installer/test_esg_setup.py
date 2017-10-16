#!/usr/bin/local/env python

import unittest
import os
import esg_setup

class test_ESG_Setup(unittest.TestCase):

	def test_download_conda(self):
		esg_setup.download_conda()
		self.assertTrue(os.path.isfile("/tmp/Miniconda2-latest-Linux-x86_64.sh"))


if __name__ == '__main__':
	unittest.main()
