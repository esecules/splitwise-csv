import unittest
import requests
import subprocess
from time import sleep
class ServerTest(unittest.TestCase):
  def test_request(self):
    serverProc = subprocess.Popen(['python', '../src/server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sleep(1)
    assertEqual(None, serverProc.poll(), "Server exited unexpectedly")
    test_data = "1234567890asdf"
    resp = requests.get("http://localhost:5000?oauth_verifier=%s" % test_data)
    assert resp.status_code == 200
    with self.assertRaises(requests.ConnectionError):
      resp = requests.get("http://localhost:5000?oauth_verifier=%s" % test_data)
    
    status = serverProc.poll()
    if status is None:  
      serverProc.kill()
      self.fail("Server process is still alive, killing now...")
    stdout, stderr = serverProc.communicate()
    
    assertFalse(stderr, "stderr is nonempty")
    assertEqual(stdout, test_data, "server didnt return fake oauth verifier!")