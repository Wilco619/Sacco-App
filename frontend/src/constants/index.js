export const API_URL = 'http://localhost:8000/api'

export const AUTH_ENDPOINTS = {
    LOGIN: `${API_URL}/token/`,
    REFRESH_TOKEN: `${API_URL}/token/refresh/`,
    VERIFY_OTP: `${API_URL}/users/verify-otp/`,
    REQUEST_OTP: `${API_URL}/users/request-otp/`
}