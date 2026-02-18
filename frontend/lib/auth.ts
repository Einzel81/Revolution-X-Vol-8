// frontend/lib/auth.ts
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'trader' | 'viewer';
  is_active: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  two_factor_code?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

class AuthService {
  private tokens: AuthTokens | null = null;

  constructor() {
    // Load tokens from localStorage on client side
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('revolution_x_auth');
      if (saved) {
        this.tokens = JSON.parse(saved);
      }
    }
  }

  getAxiosInstance() {
    const instance = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth header
    instance.interceptors.request.use((config) => {
      const token = this.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle token refresh
    instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          try {
            await this.refreshToken();
            originalRequest.headers.Authorization = `Bearer ${this.getAccessToken()}`;
            return instance(originalRequest);
          } catch (refreshError) {
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    return instance;
  }

  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await axios.post(`${API_URL}/api/v1/auth/login`, credentials);
    this.tokens = response.data;
    this.saveTokens();
    return this.tokens;
  }

  async refreshToken(): Promise<void> {
    if (!this.tokens?.refresh_token) {
      throw new Error('No refresh token');
    }

    const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
      refresh_token: this.tokens.refresh_token,
    });

    this.tokens = {
      ...this.tokens,
      access_token: response.data.access_token,
      refresh_token: response.data.refresh_token,
    };
    this.saveTokens();
  }

  async logout(): Promise<void> {
    if (this.tokens?.refresh_token) {
      try {
        await this.getAxiosInstance().post('/auth/logout', {
          refresh_token: this.tokens.refresh_token,
        });
      } catch (e) {
        // Ignore error
      }
    }
    this.clearTokens();
  }

  getAccessToken(): string | null {
    return this.tokens?.access_token || null;
  }

  getUser(): User | null {
    return this.tokens?.user || null;
  }

  isAuthenticated(): boolean {
    return !!this.tokens?.access_token;
  }

  hasRole(role: User['role'] | User['role'][]): boolean {
    const user = this.getUser();
    if (!user) return false;
    
    const roles = Array.isArray(role) ? role : [role];
    return roles.includes(user.role);
  }

  private saveTokens(): void {
    if (typeof window !== 'undefined' && this.tokens) {
      localStorage.setItem('revolution_x_auth', JSON.stringify(this.tokens));
    }
  }

  private clearTokens(): void {
    this.tokens = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('revolution_x_auth');
    }
  }
}

export const authService = new AuthService();
export const api = authService.getAxiosInstance();
