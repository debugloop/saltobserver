import saltobserver
import unittest

from redis import Redis

from scripts.generate_return_data import ReturnDataGenerator


class SaltobserverTestCase(unittest.TestCase):
    redis = Redis(connection_pool=saltobserver.redis_pool)
    rdg = ReturnDataGenerator(redis=Redis(connection_pool=saltobserver.redis_pool), minion_list=['some.minion.example.com', 'someother.minion.example.com'])

    def setUp(self):
        saltobserver.app.config['TESTING'] = True
        self.redis.flushall()
        self.app = saltobserver.app.test_client()

    def tearDown(self):
        # self.redis.flushall()
        pass

    def test_index_redirect(self):
        rv = self.app.get('/', follow_redirects=True)
        assert rv.status_code == 200
        assert '<title>Salt Observer: state.highstate</title>' in rv.data

    def test_searches(self):
        # function search
        rv = self.app.get('/functions/')
        assert rv.status_code == 200
        assert '<title>Salt Observer: Search Functions</title>' in rv.data
        rv = self.app.get('/functions/?function=state.highstate')
        assert rv.location == "http://localhost/functions/state.highstate/"
        # job search
        rv = self.app.get('/jobs/')
        assert rv.status_code == 200
        assert '<title>Salt Observer: Search Jobs</title>' in rv.data
        rv = self.app.get('/jobs/?jid=12345')
        assert rv.location == "http://localhost/jobs/12345/"
        # history search
        rv = self.app.get('/history/')
        assert rv.status_code == 200
        assert '<title>Salt Observer: Search History</title>' in rv.data
        rv = self.app.get('/history/?minion=some.minion.example.com&function=test.ping')
        assert rv.location == "http://localhost/history/some.minion.example.com/test.ping/"

    def test_empty_function(self):
        rv = self.app.get('/functions/state.highstate/')
        assert '''<h1>0</h1>
                <div class="count-title">
                    Minions have run this function...
                </div>''' in rv.data

    def test_empty_job(self):
        rv = self.app.get('/jobs/12345/')
        assert '''<h1>0</h1>
                <div class="count-title">
                    Minions have run this job.
                </div>''' in rv.data

    def test_empty_history(self):
        rv = self.app.get('/history/some.minion.example.com/state.highstate/')
        assert '''<h1>0</h1>
                <div class="count-title">
                    jobs for some.minion.example.com
                </div>''' in rv.data

    def test_count_function(self):
        self.rdg.generate(fun="state.highstate")
        rv = self.app.get('/functions/state.highstate/')
        assert '''<h1>2</h1>
                <div class="count-title">
                    Minions have run this function...
                </div>''' in rv.data
        assert '''<h1>1.0</h1>
                <div class="count-title">
                    ...time on average.
                </div>''' in rv.data
        self.rdg.generate(fun="state.highstate")
        rv = self.app.get('/functions/state.highstate/')
        assert '''<h1>2.0</h1>
                <div class="count-title">
                    ...times on average.
                </div>''' in rv.data
        # cover the case where a minion has never run the particular function
        ReturnDataGenerator(redis=Redis(connection_pool=saltobserver.redis_pool), minion_list=["onemore.minion.example.com"]).generate(jid="20150118142103074916", fun="test.ping")
        rv = self.app.get('/functions/state.highstate/')
        assert '''<h1>2</h1>
                <div class="count-title">
                    Minions have run this function...
                </div>''' in rv.data
        # cover the case where a jid is omitted because it's no valid timestamp
        self.rdg.generate(jid="1234", fun="state.highstate")
        rv = self.app.get('/functions/state.highstate/')
        assert '''<h1>0</h1>
                <div class="count-title">
                    Minions have run this function...
                </div>''' in rv.data

    def test_count_job(self):
        self.rdg.generate(jid="20150118142103074916", fun="state.highstate")
        rv = self.app.get('/jobs/20150118142103074916/')
        assert '''<h1>2</h1>
                <div class="count-title">
                    Minions have run this job.
                </div>''' in rv.data
        ReturnDataGenerator(redis=Redis(connection_pool=saltobserver.redis_pool), minion_list=["onemore.minion.example.com"]).generate(jid="20150118142103074916", fun="state.highstate")
        rv = self.app.get('/jobs/20150118142103074916/')
        assert '''<h1>3</h1>
                <div class="count-title">
                    Minions have run this job.
                </div>''' in rv.data
        # cover the case where the jid does not parse as a timestamp
        self.rdg.generate(jid="12347", fun="test.ping")
        rv = self.app.get('/jobs/12347/')
        assert '''<h1>2</h1>
                <div class="count-title">
                    Minions have run this job.
                </div>''' in rv.data

    def test_count_history(self):
        self.rdg.generate(fun="state.highstate")
        self.rdg.generate(fun="test.ping")
        rv = self.app.get('/history/some.minion.example.com/state.highstate/')
        assert '''<h1>1</h1>
                <div class="count-title">
                    job for some.minion.example.com
                </div>''' in rv.data
        self.rdg.generate(fun="state.highstate")
        rv = self.app.get('/history/some.minion.example.com/state.highstate/')
        assert '''<h1>2</h1>
                <div class="count-title">
                    jobs for some.minion.example.com
                </div>''' in rv.data
        # test with a faked jid, which causes time.strptime parsing to fail in views.py
        self.rdg.generate(jid="12345", fun="state.highstate")
        rv = self.app.get('/history/some.minion.example.com/state.highstate/')
        assert '''<h1>2</h1>
                <div class="count-title">
                    jobs for some.minion.example.com
                </div>''' in rv.data

    def test_get_data(self):
        self.rdg.generate(jid="12345", fun="state.highstate")
        rv = self.app.get('/_get_function_data/some.minion.example.com/12345/')
        assert rv.mimetype == "application/json"
        assert '"id": "some.minion.example.com"' in rv.data

if __name__ == '__main__':
    unittest.main()
