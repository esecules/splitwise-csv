import unittest
import requests
import subprocess
class ServerTest(unittest.TestCase):
  def testRequest():
    serverProc = subprocess.Popen(['python', '../src/server.py'], stdout=subprocess.PIPE, shell=True)
    test_data = "1234567890asdf"
    resp = requests.get("http://localhost:5000?oauth_verifier=%s" % testData)
    assert resp.status_code == 200
    try:
      resp = requests.get("http://localhost:5000?oauth_verifier=%s" % testData)
    except requests.exceptions.ConnectionError as e:
      pass
    else:
      self.fail("Server responded to second request (It should only serve onece and die)")
    
    status = proc.poll()
    if status is None:  
      proc.kill()
      self.fail("Server process is still alive, killing now...")
    stdout, stderr = proc.communicate()
    
    assertFalse(stderr, "stderr is nonempty")
    assertEqual(stdout, test_data, "server didnt return fake oauth verifier!")
