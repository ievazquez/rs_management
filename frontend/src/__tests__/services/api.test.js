/**
 * Tests para servicios de API
 */
import axios from 'axios';
import { authService, socialService, postService } from '../../services/api';

jest.mock('axios');

describe('authService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('login', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'test_token',
          user: {
            id: 1,
            email: 'test@example.com',
            username: 'testuser'
          }
        }
      };

      axios.post.mockResolvedValue(mockResponse);

      const result = await authService.login('test@example.com', 'password123');

      expect(axios.post).toHaveBeenCalledWith('/api/auth/login', {
        email: 'test@example.com',
        password: 'password123'
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should throw error on failed login', async () => {
      axios.post.mockRejectedValue(new Error('Invalid credentials'));

      await expect(
        authService.login('wrong@example.com', 'wrongpass')
      ).rejects.toThrow('Invalid credentials');
    });
  });

  describe('register', () => {
    it('should register new user successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'new_token',
          user: {
            id: 2,
            email: 'newuser@example.com',
            username: 'newuser'
          }
        }
      };

      axios.post.mockResolvedValue(mockResponse);

      const userData = {
        email: 'newuser@example.com',
        username: 'newuser',
        password: 'password123'
      };

      const result = await authService.register(userData);

      expect(axios.post).toHaveBeenCalledWith('/api/auth/register', userData);
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getCurrentUser', () => {
    it('should get current user', async () => {
      const mockResponse = {
        data: {
          id: 1,
          email: 'test@example.com',
          username: 'testuser'
        }
      };

      axios.get.mockResolvedValue(mockResponse);

      const result = await authService.getCurrentUser();

      expect(axios.get).toHaveBeenCalledWith('/api/auth/me');
      expect(result).toEqual(mockResponse.data);
    });
  });
});

describe('socialService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getConnectedAccounts', () => {
    it('should fetch connected accounts', async () => {
      const mockAccounts = [
        {
          id: 1,
          platform: 'facebook',
          platform_username: 'testfb',
          is_active: true
        },
        {
          id: 2,
          platform: 'twitter',
          platform_username: 'testtw',
          is_active: true
        }
      ];

      axios.get.mockResolvedValue({ data: mockAccounts });

      const result = await socialService.getConnectedAccounts();

      expect(axios.get).toHaveBeenCalledWith('/api/social/accounts');
      expect(result).toEqual(mockAccounts);
      expect(result).toHaveLength(2);
    });
  });

  describe('connectAccount', () => {
    it('should connect social account', async () => {
      const mockAccount = {
        id: 3,
        platform: 'instagram',
        platform_username: 'testig'
      };

      axios.post.mockResolvedValue({ data: mockAccount });

      const result = await socialService.connectAccount(
        'instagram',
        'auth_code_123',
        'http://localhost:3000/callback'
      );

      expect(axios.post).toHaveBeenCalledWith('/api/social/connect', {
        platform: 'instagram',
        code: 'auth_code_123',
        redirect_uri: 'http://localhost:3000/callback'
      });
      expect(result).toEqual(mockAccount);
    });
  });

  describe('disconnectAccount', () => {
    it('should disconnect account', async () => {
      axios.delete.mockResolvedValue({ data: { message: 'Success' } });

      const result = await socialService.disconnectAccount(1);

      expect(axios.delete).toHaveBeenCalledWith('/api/social/disconnect/1');
      expect(result.message).toBe('Success');
    });
  });
});

describe('postService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('createPost', () => {
    it('should create post successfully', async () => {
      const mockPost = {
        id: 1,
        content: 'Test post',
        status: 'draft',
        platforms: []
      };

      axios.post.mockResolvedValue({ data: mockPost });

      const postData = {
        content: 'Test post',
        platform_account_ids: [1, 2]
      };

      const result = await postService.createPost(postData);

      expect(axios.post).toHaveBeenCalledWith('/api/posts/', postData);
      expect(result).toEqual(mockPost);
    });
  });

  describe('getPosts', () => {
    it('should fetch posts with pagination', async () => {
      const mockPosts = [
        { id: 1, content: 'Post 1', status: 'published' },
        { id: 2, content: 'Post 2', status: 'draft' }
      ];

      axios.get.mockResolvedValue({ data: mockPosts });

      const result = await postService.getPosts(0, 20);

      expect(axios.get).toHaveBeenCalledWith('/api/posts/?skip=0&limit=20');
      expect(result).toEqual(mockPosts);
    });
  });

  describe('publishPost', () => {
    it('should publish post', async () => {
      const mockResponse = {
        id: 1,
        status: 'publishing'
      };

      axios.post.mockResolvedValue({ data: mockResponse });

      const result = await postService.publishPost(1);

      expect(axios.post).toHaveBeenCalledWith('/api/posts/1/publish');
      expect(result.status).toBe('publishing');
    });
  });

  describe('deletePost', () => {
    it('should delete post', async () => {
      axios.delete.mockResolvedValue({ data: { message: 'Deleted' } });

      const result = await postService.deletePost(1);

      expect(axios.delete).toHaveBeenCalledWith('/api/posts/1');
      expect(result.message).toBe('Deleted');
    });
  });
});
