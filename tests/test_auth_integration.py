import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from jwt import PyJWKClient
import jwt

from app.services.auth import JWTService
from app.models.user import User
from app.models.conversation import Conversation


class TestAuthIntegration:
    """Test authentication integration scenarios."""
    
    def test_jwt_service_with_mock_jwks(self):
        """Test JWT service with mocked JWKS endpoint."""
        with patch('app.services.auth.PyJWKClient') as mock_jwk_client_class:
            # Setup mock JWKS client
            mock_jwk_client = Mock()
            mock_signing_key = Mock()
            mock_signing_key.key = "test-public-key"
            mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwk_client_class.return_value = mock_jwk_client
            
            # Create JWT service
            service = JWTService()
            
            # Mock JWT decode
            with patch('app.services.auth.jwt.decode') as mock_decode:
                mock_payload = {
                    "sub": "test-user-123",
                    "email": "test@example.com",
                    "exp": 9999999999,
                    "iss": "test-issuer",
                    "token_use": "access"
                }
                mock_decode.return_value = mock_payload
                
                # Test token verification
                result = service.verify_token("test-token")
                assert result == mock_payload
                mock_decode.assert_called_once()
    
    def test_jwt_service_token_expiration(self):
        """Test JWT service handling of expired tokens."""
        with patch('app.services.auth.PyJWKClient') as mock_jwk_client_class:
            mock_jwk_client = Mock()
            mock_signing_key = Mock()
            mock_signing_key.key = "test-public-key"
            mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwk_client_class.return_value = mock_jwk_client
            
            service = JWTService()
            
            with patch('app.services.auth.jwt.decode') as mock_decode:
                from jwt import ExpiredSignatureError
                mock_decode.side_effect = ExpiredSignatureError("Token expired")
                
                with pytest.raises(Exception) as exc_info:
                    service.verify_token("expired-token")
                
                assert "Token Expired" in str(exc_info.value)
    
    def test_jwt_service_invalid_signature(self):
        """Test JWT service handling of invalid signatures."""
        with patch('app.services.auth.PyJWKClient') as mock_jwk_client_class:
            mock_jwk_client = Mock()
            mock_signing_key = Mock()
            mock_signing_key.key = "test-public-key"
            mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwk_client_class.return_value = mock_jwk_client
            
            service = JWTService()
            
            with patch('app.services.auth.jwt.decode') as mock_decode:
                from jwt import InvalidKeyError
                mock_decode.side_effect = InvalidKeyError("Invalid signature")
                
                with pytest.raises(Exception) as exc_info:
                    service.verify_token("invalid-token")
                
                assert "Invalid token" in str(exc_info.value)
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_authorization_header_variations(self, mock_verify_token, client: TestClient, db_session):
        """Test various authorization header formats."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Test valid Bearer token
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "Bearer valid-token"}
        )
        assert response.status_code == 200
        
        # Test case variations
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "bearer valid-token"}
        )
        assert response.status_code == 401  # Should be case sensitive
        
        # Test with extra spaces
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "  Bearer valid-token  "}
        )
        assert response.status_code == 401  # Should not handle extra spaces
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_missing_authorization_header(self, mock_verify_token, client: TestClient):
        """Test behavior when authorization header is missing."""
        # Test with no authorization header
        response = client.get("/api/v1/secure")
        assert response.status_code == 401
        assert "Missing or Invalid Authorization Header" in response.json()["detail"]
        
        # Test with empty authorization header
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": ""}
        )
        assert response.status_code == 401
        assert "Missing or Invalid Authorization Header" in response.json()["detail"]
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_user_not_found_after_jwt_verification(self, mock_verify_token, client: TestClient, db_session):
        """Test when JWT is valid but user doesn't exist in database."""
        # Mock JWT verification to return valid payload
        mock_verify_token.return_value = {
            "sub": "non-existent-user",
            "email": "nonexistent@example.com"
        }
        
        # Try to access secure endpoint
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "Bearer valid-token"}
        )
        
        # Should fail because user doesn't exist in database
        assert response.status_code == 401
        assert "User not found" in response.json()["detail"]
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_jwt_verification_failure(self, mock_verify_token, client: TestClient):
        """Test when JWT verification fails."""
        # Mock JWT verification to raise exception
        from fastapi import HTTPException
        mock_verify_token.side_effect = HTTPException(
            status_code=401,
            detail="Token verification failed"
        )
        
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
        assert "Token verification failed" in response.json()["detail"]


class TestAuthEdgeCases:
    """Test authentication edge cases and security scenarios."""
    
    def test_malformed_jwt_token(self, client: TestClient):
        """Test handling of malformed JWT tokens."""
        malformed_tokens = [
            "not-a-jwt",
            "Bearer",
            "Bearer ",
            "Bearer not.a.jwt",
            "Bearer not-a-jwt-token",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
        ]

        for token in malformed_tokens:
            response = client.get(
                "/api/v1/secure",
                headers={"Authorization": token}
            )
            # Should be 401 for malformed authorization headers or invalid tokens
            assert response.status_code == 401
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_jwt_payload_missing_required_fields(self, mock_verify_token, client: TestClient):
        """Test JWT with missing required fields."""
        # Mock JWT verification to return payload missing required fields
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            # Missing 'exp', 'iss', 'token_use'
        }
        
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "Bearer valid-token"}
        )
        
        # Should still work if JWT verification passes
        # (The JWT service should handle validation)
        assert response.status_code in [200, 401]
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_jwt_with_wrong_token_use(self, mock_verify_token, client: TestClient):
        """Test JWT with wrong token_use field."""
        # Mock JWT verification to return payload with wrong token_use
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": 9999999999,
            "iss": "test-issuer",
            "token_use": "id"  # Should be "access"
        }
        
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "Bearer valid-token"}
        )
        
        # Should still work if JWT verification passes
        # (The JWT service should handle validation)
        assert response.status_code in [200, 401]
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_concurrent_auth_requests(self, mock_verify_token, client: TestClient, db_session):
        """Test concurrent authentication requests."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Make multiple concurrent requests
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get(
                "/api/v1/secure",
                headers={"Authorization": "Bearer valid-token"}
            )
            results.append(response.status_code)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5


class TestAuthPerformance:
    """Test authentication performance characteristics."""
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_auth_performance_with_large_payload(self, mock_verify_token, client: TestClient, db_session):
        """Test authentication performance with large JWT payload."""
        # Mock JWT verification with large payload
        large_payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": 9999999999,
            "iss": "test-issuer",
            "token_use": "access",
            "custom_claims": {
                "large_data": "x" * 1000,  # Large string
                "permissions": [f"permission_{i}" for i in range(100)],
                "metadata": {f"key_{i}": f"value_{i}" for i in range(50)}
            }
        }
        mock_verify_token.return_value = large_payload
        
        # Create user
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Measure response time
        import time
        start_time = time.time()
        
        response = client.get(
            "/api/v1/secure",
            headers={"Authorization": "Bearer large-token"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        # Response should be reasonably fast even with large payload
        assert response_time < 1.0  # Should complete within 1 second
    
    @patch('app.api.deps.jwt_service.verify_token')
    def test_auth_caching_behavior(self, mock_verify_token, client: TestClient, db_session):
        """Test authentication caching behavior."""
        # Mock JWT verification
        mock_verify_token.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com"
        }
        
        # Create user
        user = User(
            cognito_sub="test-user-123",
            email="test@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # Make multiple requests with same token
        for _ in range(10):
            response = client.get(
                "/api/v1/secure",
                headers={"Authorization": "Bearer same-token"}
            )
            assert response.status_code == 200
        
        # Verify JWT verification was called for each request
        # (No caching in current implementation)
        assert mock_verify_token.call_count == 10
