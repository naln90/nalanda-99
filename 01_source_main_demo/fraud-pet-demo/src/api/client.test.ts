import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './client';

describe('api client', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('posts demo login and returns the current user payload', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({
        currentUser: {
          ownerId: 'U-2408**',
          hasCompletedAssessment: false,
          hasPet: false,
        },
      }),
    } as Response);

    const result = await api.demoLogin('U-2408**');

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/demo-login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ ownerId: 'U-2408**' }),
      }),
    );
    expect(result.currentUser.ownerId).toBe('U-2408**');
  });
});
