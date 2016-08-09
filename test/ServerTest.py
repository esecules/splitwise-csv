import unittest
import requests
import subprocess
from time import sleep
class ServerTest(unittest.TestCase):
  def test_request(self):
    serverProc = subprocess.Popen(['python', '../src/server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sleep(1)
    self.assertEqual(None, serverProc.poll())
    test_data = "1234567890asdf"
    resp = requests.get("http://localhost:5000?oauth_verifier=%s" % test_data)
    assert resp.status_code == 200
    with self.assertRaises(requests.ConnectionError):
      resp = requests.get("http://localhost:5000?oauth_verifier=%s" % test_data)

    polls = 0
    while serverProc.poll() is None and polls < 10:
      polls += 1
      sleep(1)

    status = serverProc.poll()  
    if status is None:
      serverProc.kill()
      self.fail("Server process is still alive, killing now...")
    stdout, _ = serverProc.communicate()

    self.assertEqual(0, status, "Server exited with nonzero status: %s" % status)
    self.assertEqual(test_data, stdout, "server didnt return fake oauth verifier, instead: '%s'" % stdout)
