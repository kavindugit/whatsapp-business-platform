import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { authApi } from '../api/auth';
import { useAuth } from '../app/AuthContext';
import { parseApiError } from '../api/errors';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginForm) => {
    try {
      setError(null);
      const res = await authApi.login(data.email, data.password);
      // Store CSRF in React memory via AuthContext — NOT localStorage.
      login(res.data.csrf_token, res.data);

      const from = (location.state as { from?: Location })?.from?.pathname ?? '/workspaces';
      navigate(from, { replace: true });
    } catch (err) {
      setError(parseApiError(err));
    }
  };

  return (
    <Card>
      <form onSubmit={handleSubmit(onSubmit)} className="flex-col gap-4" noValidate>
        {error && (
          <div
            role="alert"
            className="text-sm text-center"
            style={{
              padding: 'var(--space-2) var(--space-3)',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-danger-400)',
            }}
          >
            {error}
          </div>
        )}

        <Input
          id="login-email"
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="name@company.com"
          {...register('email')}
          error={errors.email?.message}
        />

        <Input
          id="login-password"
          label="Password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          {...register('password')}
          error={errors.password?.message}
        />

        <Button
          id="login-submit"
          type="submit"
          className="mt-4"
          style={{ width: '100%' }}
          isLoading={isSubmitting}
        >
          Sign In
        </Button>
      </form>
    </Card>
  );
};
