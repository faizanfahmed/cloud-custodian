# Copyright 2016 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from botocore.exceptions import ClientError

from c7n.iamaccess import CrossAccountAccessFilter
from c7n.manager import resources
from c7n.query import QueryResourceManager
from c7n.utils import local_session


@resources.register('lambda')
class AWSLambda(QueryResourceManager):

    resource_type = "aws.lambda.function"


@AWSLambda.filter_registry.register('cross-account')
class LambdaCrossAccountAccessFilter(CrossAccountAccessFilter):

    def process(self, resources, event=None):

        def _augment(r):
            client = local_session(
                self.manager.session_factory).client('lambda')
            try:
                r['Policy'] = client.get_policy(
                    FunctionName=r['FunctionName'])['Policy']
                return r
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDeniedException':
                    self.log.warning(
                        "Access denied getting policy lambda:%s",
                        r['FunctionName'])

        self.log.debug("fetching policy for %d lambdas" % len(resources))
        with self.executor_factory(max_workers=3) as w:
            resources = filter(None, w.map(_augment, resources))

        return super(LambdaCrossAccountAccessFilter, self).process(
            resources, event)
