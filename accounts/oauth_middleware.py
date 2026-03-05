
import logging
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from .models import OAuthToken

logger = logging.getLogger(__name__)


class OAuthTokenMiddleware(MiddlewareMixin):
    """
    Middleware to automatically refresh expired OAuth tokens.

    This middleware checks if the authenticated user has an OAuth token
    and automatically refreshes it if it's about to expire.
    """

    def process_request(self, request):
        """Check and refresh OAuth token on each request"""


        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        try:

            oauth_token = OAuthToken.objects.get(user=request.user)


            if oauth_token.is_expired():
                logger.info(f"OAuth token expired for user {request.user.username}")


                refresh_result = oauth_token.refresh_access_token()

                if not refresh_result:
                    logger.warning(f"Failed to refresh OAuth token for user {request.user.username}")

                    logout(request)
                    return redirect('accounts:hemis_login')
                else:
                    logger.info(f"Successfully refreshed OAuth token for user {request.user.username}")

        except OAuthToken.DoesNotExist:

            pass
        except Exception as e:
            logger.error(f"Error processing OAuth token for user {request.user.username}: {str(e)}")


        return None
