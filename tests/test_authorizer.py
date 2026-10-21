
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'foundation'))

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock

from auth.authorizer import Authorizer, AuthData, AuthError, parse_roles

#-------------------------------------------------------------------------------
# Helpers

def make_request(authorization=None):
	request = MagicMock()
	request.headers.get.return_value = authorization
	request.parse_locale_priority.return_value = []
	return request


def make_jwt(claims=None):
	jwt = MagicMock()
	jwt.validate_token.return_value = claims
	return jwt


def make_claims(sub='user1', jti='jti-abc', roles='', iat_offset=-10, exp_offset=3600):
	now = int(datetime.now(timezone.utc).timestamp())
	return {
		'sub': sub,
		'jti': jti,
		'iat': now + iat_offset,
		'exp': now + exp_offset,
		'roles': roles,
	}


@pytest.fixture
def authorizer():
	return Authorizer(make_jwt())

#-------------------------------------------------------------------------------
# parse_roles

def testParseRolesEmpty():
	assert list(parse_roles({'roles': ''})) == []

def testParseRolesSingle():
	assert list(parse_roles({'roles': '3'})) == [3]

def testParseRolesMultiple():
	assert list(parse_roles({'roles': '1,2,3'})) == [1, 2, 3]

def testParseRolesIgnoresTrailingComma():
	assert list(parse_roles({'roles': '1,2,'})) == [1, 2]

#-------------------------------------------------------------------------------
# grep_token_claims

def testGrepMissingHeaderReturnsMissingToken(authorizer):
	request = make_request(authorization=None)
	ok, outcome = authorizer.grep_token_claims(request)
	assert not ok
	assert outcome is AuthError.MISSING_TOKEN

def testGrepMalformedHeaderReturnsMissingToken(authorizer):
	request = make_request(authorization='Token abc123')
	ok, outcome = authorizer.grep_token_claims(request)
	assert not ok
	assert outcome is AuthError.MISSING_TOKEN

def testGrepInvalidTokenReturnsInvalidToken(authorizer):
	authorizer.jwt_manager = make_jwt(claims=None)
	request = make_request(authorization='Bearer bad.token.here')
	ok, outcome = authorizer.grep_token_claims(request)
	assert not ok
	assert outcome is AuthError.INVALID_TOKEN

def testGrepValidTokenReturnsClaims(authorizer):
	claims = make_claims()
	authorizer.jwt_manager = make_jwt(claims=claims)
	request = make_request(authorization='Bearer valid.token.here')
	ok, outcome = authorizer.grep_token_claims(request)
	assert ok
	assert outcome is claims

#-------------------------------------------------------------------------------
# validate_access — token extraction errors

@pytest.mark.asyncio
async def testValidateAccessMissingToken(authorizer):
	request = make_request()
	ok, outcome = await authorizer.validate_access(request, {})
	assert not ok
	assert outcome is AuthError.MISSING_TOKEN

@pytest.mark.asyncio
async def testValidateAccessInvalidToken(authorizer):
	authorizer.jwt_manager = make_jwt(claims=None)
	request = make_request(authorization='Bearer bad.token.here')
	ok, outcome = await authorizer.validate_access(request, {})
	assert not ok
	assert outcome is AuthError.INVALID_TOKEN

#-------------------------------------------------------------------------------
# validate_access — disabled endpoint

@pytest.mark.asyncio
async def testValidateAccessDisabledEndpoint(authorizer):
	authorizer.disabled.add(('pkg', 'func'))
	request = make_request()
	ok, outcome = await authorizer.validate_access(
		request, {'package': 'pkg', 'functionality': 'func'})
	assert not ok
	assert outcome is AuthError.DISABLED_ENDPOINT

#-------------------------------------------------------------------------------
# validate_access — mark_modified / expired auth

@pytest.mark.asyncio
async def testValidateAccessExpiredAfterMarkModified(authorizer):
	claims = make_claims(sub='user1', iat_offset=-100)
	authorizer.jwt_manager = make_jwt(claims=claims)
	authorizer.mark_modified('user1')
	request = make_request(authorization='Bearer valid.token.here')
	ok, outcome = await authorizer.validate_access(request, {})
	assert not ok
	assert outcome is AuthError.EXPIRED_AUTH

@pytest.mark.asyncio
async def testValidateAccessNotExpiredIfIssuedAfterModification(authorizer):
	authorizer.mark_modified('user1')
	claims = make_claims(sub='user1', iat_offset=10)
	authorizer.jwt_manager = make_jwt(claims=claims)
	request = make_request(authorization='Bearer valid.token.here')
	ok, outcome = await authorizer.validate_access(request, {})
	assert ok

#-------------------------------------------------------------------------------
# validate_access — blacklist

@pytest.mark.asyncio
async def testValidateAccessBlacklistedToken(authorizer):
	claims = make_claims(sub='user1', jti='blocked-jti')
	authorizer.jwt_manager = make_jwt(claims=claims)
	authorizer.blacklisted[('user1', 'blocked-jti')] = claims['exp']
	request = make_request(authorization='Bearer valid.token.here')
	ok, outcome = await authorizer.validate_access(request, {})
	assert not ok
	assert outcome is AuthError.BLOCKED_USER

#-------------------------------------------------------------------------------
# validate_access — functionality / role checks

@pytest.mark.asyncio
async def testValidateAccessNotAllowedWithNoRoles(authorizer):
	claims = make_claims(roles='')
	authorizer.jwt_manager = make_jwt(claims=claims)
	request = make_request(authorization='Bearer valid.token.here')
	ok, outcome = await authorizer.validate_access(
		request, {'package': 'pkg', 'functionality': 'func'})
	assert not ok
	assert outcome is AuthError.NOT_ALLOWED

@pytest.mark.asyncio
async def testValidateAccessNotAllowedWithWrongRole(authorizer):
	claims = make_claims(roles='99')
	authorizer.jwt_manager = make_jwt(claims=claims)
	authorizer.roles_access[1] = {('pkg', 'func')}
	request = make_request(authorization='Bearer valid.token.here')
	ok, outcome = await authorizer.validate_access(
		request, {'package': 'pkg', 'functionality': 'func'})
	assert not ok
	assert outcome is AuthError.NOT_ALLOWED

@pytest.mark.asyncio
async def testValidateAccessAllowedWithMatchingRole(authorizer):
	claims = make_claims(roles='1')
	authorizer.jwt_manager = make_jwt(claims=claims)
	authorizer.roles_access[1] = {('pkg', 'func')}
	request = make_request(authorization='Bearer valid.token.here')
	ok, auth_data = await authorizer.validate_access(
		request, {'package': 'pkg', 'functionality': 'func'})
	assert ok
	assert isinstance(auth_data, AuthData)
	assert auth_data.account_id == 'user1'

@pytest.mark.asyncio
async def testValidateAccessAllowedWithOneOfMultipleRoles(authorizer):
	claims = make_claims(roles='2,5')
	authorizer.jwt_manager = make_jwt(claims=claims)
	authorizer.roles_access[5] = {('pkg', 'func')}
	request = make_request(authorization='Bearer valid.token.here')
	ok, _ = await authorizer.validate_access(
		request, {'package': 'pkg', 'functionality': 'func'})
	assert ok

@pytest.mark.asyncio
async def testValidateAccessNoFunctionalitySkipsRoleCheck(authorizer):
	claims = make_claims(roles='')
	authorizer.jwt_manager = make_jwt(claims=claims)
	request = make_request(authorization='Bearer valid.token.here')
	ok, auth_data = await authorizer.validate_access(request, {})
	assert ok
	assert isinstance(auth_data, AuthData)

#-------------------------------------------------------------------------------
# validate_access — expired token

@pytest.mark.asyncio
async def testValidateAccessExpiredToken(authorizer):
	claims = make_claims(exp_offset=-1)
	authorizer.jwt_manager = make_jwt(claims=claims)
	request = make_request(authorization='Bearer valid.token.here')
	ok, outcome = await authorizer.validate_access(request, {})
	assert not ok
	assert outcome is AuthError.EXPIRED_AUTH

#-------------------------------------------------------------------------------
# validate_access — returned AuthData fields

@pytest.mark.asyncio
async def testValidateAccessReturnsCorrectAuthData(authorizer):
	claims = make_claims(sub='user42', jti='jti-xyz')
	authorizer.jwt_manager = make_jwt(claims=claims)
	request = make_request(authorization='Bearer valid.token.here')
	ok, auth_data = await authorizer.validate_access(request, {})
	assert ok
	assert auth_data.account_id == 'user42'
	assert auth_data.jti == 'jti-xyz'
	assert auth_data.expiration == claims['exp']

#-------------------------------------------------------------------------------
# blacklist / clear_blacklist

def testBlacklistStoresEntry(authorizer):
	auth_data = AuthData('user1', 'jti-abc', expiration=9999999999)
	authorizer.blacklist(auth_data)
	assert ('user1', 'jti-abc') in authorizer.blacklisted

def testClearBlacklistRemovesExpiredEntries(authorizer):
	past = int(datetime.now(timezone.utc).timestamp()) - 1
	future = int(datetime.now(timezone.utc).timestamp()) + 3600
	authorizer.blacklisted[('u1', 'j1')] = past
	authorizer.blacklisted[('u2', 'j2')] = future
	removed = authorizer.clear_blacklist()
	assert removed == 1
	assert ('u1', 'j1') not in authorizer.blacklisted
	assert ('u2', 'j2') in authorizer.blacklisted

def testClearBlacklistReturnsZeroWhenNothingExpired(authorizer):
	future = int(datetime.now(timezone.utc).timestamp()) + 3600
	authorizer.blacklisted[('u1', 'j1')] = future
	assert authorizer.clear_blacklist() == 0

def testClearBlacklistEmptyBlacklist(authorizer):
	assert authorizer.clear_blacklist() == 0

#-------------------------------------------------------------------------------
# mark_modified

def testMarkModifiedStoresTimestamp(authorizer):
	before = int(datetime.now(timezone.utc).timestamp())
	authorizer.mark_modified('user1')
	after = int(datetime.now(timezone.utc).timestamp())
	ts = authorizer.users_modification['user1']
	assert before <= ts <= after

def testMarkModifiedOverwritesPreviousTimestamp(authorizer):
	authorizer.mark_modified('user1')
	first = authorizer.users_modification['user1']
	authorizer.mark_modified('user1')
	second = authorizer.users_modification['user1']
	assert second >= first

#-------------------------------------------------------------------------------
# enable / disable functionality

@pytest.mark.asyncio
async def testDisableFunctionalityAddsToDisabledSet(authorizer):
	db = AsyncMock()
	db.fetchrow.return_value = ('pkg', 'func')
	result = await authorizer.disable_functionality(db, 42)
	assert result is True
	assert ('pkg', 'func') in authorizer.disabled

@pytest.mark.asyncio
async def testDisableFunctionalityReturnsFalseWhenNotFound(authorizer):
	db = AsyncMock()
	db.fetchrow.return_value = None
	result = await authorizer.disable_functionality(db, 99)
	assert result is False

@pytest.mark.asyncio
async def testEnableFunctionalityRemovesFromDisabledSet(authorizer):
	authorizer.disabled.add(('pkg', 'func'))
	db = AsyncMock()
	db.fetchrow.return_value = ('pkg', 'func')
	result = await authorizer.enable_functionality(db, 42)
	assert result is True
	assert ('pkg', 'func') not in authorizer.disabled

@pytest.mark.asyncio
async def testEnableFunctionalityReturnsFalseWhenNotFound(authorizer):
	db = AsyncMock()
	db.fetchrow.return_value = None
	result = await authorizer.enable_functionality(db, 99)
	assert result is False

#-------------------------------------------------------------------------------
# allow_access / remove_access

@pytest.mark.asyncio
async def testAllowAccessAddsToRolesAccess(authorizer):
	db = AsyncMock()
	db.fetchrow.return_value = ('pkg', 'func')
	await authorizer.allow_access(db, functionality_id=1, role_id=5)
	assert ('pkg', 'func') in authorizer.roles_access[5]

@pytest.mark.asyncio
async def testAllowAccessNoopWhenFunctionalityNotFound(authorizer):
	db = AsyncMock()
	db.fetchrow.return_value = None
	await authorizer.allow_access(db, functionality_id=1, role_id=5)
	assert 5 not in authorizer.roles_access

@pytest.mark.asyncio
async def testRemoveAccessDiscardsFromRolesAccess(authorizer):
	authorizer.roles_access[5] = {('pkg', 'func')}
	db = AsyncMock()
	db.fetchrow.return_value = ('pkg', 'func')
	await authorizer.remove_access(db, functionality_id=1, role_id=5)
	assert ('pkg', 'func') not in authorizer.roles_access[5]

#-------------------------------------------------------------------------------
# list_accesses

def testListAccessesReturnsEmptyForInvalidToken(authorizer):
	authorizer.jwt_manager = make_jwt(claims=None)
	request = make_request(authorization='Bearer bad.token')
	assert authorizer.list_accesses(request) == tuple()

def testListAccessesReturnsUserFunctionalities(authorizer):
	claims = make_claims(roles='1,2')
	authorizer.jwt_manager = make_jwt(claims=claims)
	authorizer.roles_access[1] = {('pkg', 'funcA')}
	authorizer.roles_access[2] = {('pkg', 'funcB')}
	request = make_request(authorization='Bearer valid.token.here')
	accesses = set(authorizer.list_accesses(request))
	assert ('pkg', 'funcA') in accesses
	assert ('pkg', 'funcB') in accesses

def testListAccessesDeduplicatesOverlappingRoles(authorizer):
	claims = make_claims(roles='1,2')
	authorizer.jwt_manager = make_jwt(claims=claims)
	authorizer.roles_access[1] = {('pkg', 'func')}
	authorizer.roles_access[2] = {('pkg', 'func')}
	request = make_request(authorization='Bearer valid.token.here')
	assert len(authorizer.list_accesses(request)) == 1

#-------------------------------------------------------------------------------

if __name__ == '__main__':
	pytest.main([__file__, '-v'])
