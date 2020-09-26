Install using `pip`:
```
pip install bitbucket-python-client
```

Optionally set `BITBUCKET_URL`:
```bash
export BITBUCKET_URL=https://bitbucket.company.tld
```

Create client:
```
from bitbucket import Bitbucket

client = Bitbucket(token='MDk5MzM4NTY2ODAwOshm4zdyh0xdJ0VPR7o7zBNZcuQy')

```

Raise pull request:
```
client.create_pullrequest(project='AG', repository='repo1-toolkit', source_branch='develop', target_branch='master', title='My first PR', description="Testing"))
```
