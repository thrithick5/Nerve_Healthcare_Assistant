# Vercel Environment Variables
# 
# These must be configured in the Vercel dashboard for the sign-in to work.
# Go to: https://vercel.com/account/projects/nerve-healthcare-assistant/settings/environment-variables
#
# Required variables:
#
# 1. VITE_API_BASE_URL
#    Value: https://nerve-healthcare-backend.onrender.com/api
#    Environments: Production, Preview
#
# 2. VITE_GOOGLE_CLIENT_ID
#    Value: 388676578583-74qqn1h809fk1j9qckrajakt78hutanl.apps.googleusercontent.com
#    Environments: Production, Preview
#
# Without VITE_GOOGLE_CLIENT_ID, Google sign-in will silently fail.
# The @react-oauth/google component requires this to be set at build time.
