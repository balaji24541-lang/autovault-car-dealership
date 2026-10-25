import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

const vehicle = { id: 1, make: 'Toyota', model: 'Camry', category: 'Sedan', price: '24500.00', quantity: 2 };
const response = (data: unknown, status = 200) => ({ ok: status < 400, status, json: async () => data });

afterEach(() => { cleanup(); localStorage.clear(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

it('renders login form for anonymous users', () => {
  render(<App />);
  expect(screen.getByText('Sign in to your account')).toBeTruthy();
  expect(screen.getByLabelText('Email address')).toBeTruthy();
});

it('shows registration form and submits valid registration', async () => {
  const fetch = vi.fn().mockResolvedValue(response({ message: 'Account created' }));
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  fireEvent.click(screen.getByText('Register'));
  expect(screen.getByText('Create your account')).toBeTruthy();
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'new@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Customer123' } });
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }));
  await screen.findByText('Account created. Please sign in.');
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/auth/register'), expect.objectContaining({ method: 'POST' }));
});

it('logs in and shows vehicle data and totals from the API', async () => {
  const fetch = vi.fn()
    .mockResolvedValueOnce(response({ access_token: 'valid-token', role: 'customer' }))
    .mockResolvedValueOnce(response([vehicle]));
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'user@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Customer123' } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  await screen.findByText('Toyota Camry');
  expect(screen.getByText('$24,500')).toBeTruthy();
  expect(screen.getByText('2')).toBeTruthy();
  fireEvent.click(screen.getByText('Logout'));
  expect(screen.getByText('Sign in to your account')).toBeTruthy();
});

it('shows a useful error when login fails', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ detail: 'Invalid credentials' }, 401)));
  render(<App />);
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'user@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'incorrect1' } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  expect((await screen.findByRole('alert')).textContent).toContain('Invalid credentials');
});

it('filters inventory by make, category, and minimum and maximum prices', async () => {
  localStorage.setItem('token', 'valid-token');
  localStorage.setItem('role', 'customer');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response([
    vehicle,
    { ...vehicle, id: 2, make: 'Honda', model: 'Civic', category: 'Compact', price: '19000.00', quantity: 0 },
  ])));
  render(<App />);
  await screen.findByText('Toyota Camry');
  fireEvent.change(screen.getByLabelText('Search vehicles'), { target: { value: 'Honda' } });
  expect(screen.getByText('Honda Civic')).toBeTruthy();
  expect(screen.queryByText('Toyota Camry')).toBeNull();
  fireEvent.change(screen.getByLabelText('Search vehicles'), { target: { value: '' } });
  fireEvent.change(screen.getByLabelText('Category'), { target: { value: 'Sedan' } });
  fireEvent.change(screen.getByLabelText('Minimum price'), { target: { value: '20000' } });
  fireEvent.change(screen.getByLabelText('Maximum price'), { target: { value: '30000' } });
  expect(screen.getByText('Toyota Camry')).toBeTruthy();
  expect(screen.queryByText('Honda Civic')).toBeNull();
});

it('shows an empty state and reports inventory API errors', async () => {
  localStorage.setItem('token', 'valid-token');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response([])));
  render(<App />);
  expect(await screen.findByText(/No vehicles found/)).toBeTruthy();
  cleanup();
  localStorage.setItem('token', 'valid-token');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ...response({ detail: 'Service unavailable' }, 503) }));
  render(<App />);
  await waitFor(() => expect(screen.getByText('Service unavailable')).toBeTruthy());
});

it('disables purchase when a vehicle has no stock', async () => {
  localStorage.setItem('token', 'valid-token');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response([{ ...vehicle, quantity: 0 }])));
  render(<App />);
  await screen.findByText('Toyota Camry');
  expect(screen.getByRole('button', { name: 'Purchase vehicle' })).toHaveProperty('disabled', true);
});

it('confirms a purchase and refreshes the displayed stock', async () => {
  localStorage.setItem('token', 'valid-token');
  const fetch = vi.fn()
    .mockResolvedValueOnce(response([{ ...vehicle, quantity: 1 }]))
    .mockResolvedValueOnce(response({ ...vehicle, quantity: 0 }))
    .mockResolvedValueOnce(response([{ ...vehicle, quantity: 0 }]));
  vi.stubGlobal('fetch', fetch);
  vi.spyOn(window, 'confirm').mockReturnValue(true);
  render(<App />);
  await screen.findByText('Toyota Camry');
  fireEvent.click(screen.getByRole('button', { name: 'Purchase vehicle' }));
  expect(await screen.findByText('0 available')).toBeTruthy();
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/purchase'), expect.objectContaining({ method: 'POST' }));
});

it('lets an admin submit a valid new vehicle', async () => {
  localStorage.setItem('token', 'valid-token');
  localStorage.setItem('role', 'admin');
  const fetch = vi.fn()
    .mockResolvedValueOnce(response([]))
    .mockResolvedValueOnce(response(vehicle, 201))
    .mockResolvedValueOnce(response([vehicle]));
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  await screen.findByText('No vehicles found. Add your first vehicle to get started.');
  fireEvent.click(screen.getByRole('button', { name: /Add vehicle/ }));
  for (const [name, value] of [['make', 'Toyota'], ['model', 'Camry'], ['category', 'Sedan'], ['price', '24500'], ['quantity', '2']]) {
    fireEvent.change(screen.getByLabelText(name, { selector: 'input' }), { target: { value } });
  }
  fireEvent.click(screen.getByRole('button', { name: 'Save vehicle' }));
  expect(await screen.findByText('Toyota Camry')).toBeTruthy();
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/vehicles'), expect.objectContaining({ method: 'POST' }));
});

it('shows admin controls only for an admin account', async () => {
  localStorage.setItem('token', 'valid-token');
  localStorage.setItem('role', 'admin');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response([vehicle])));
  render(<App />);
  await screen.findByText('Toyota Camry');
  expect(screen.getByRole('button', { name: /Add vehicle/ })).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Edit' })).toBeTruthy();
});

it('does not show inventory management controls to customers', async () => {
  localStorage.setItem('token', 'valid-token');
  localStorage.setItem('role', 'customer');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response([vehicle])));
  render(<App />);
  await screen.findByText('Toyota Camry');
  expect(screen.queryByRole('button', { name: /Add vehicle/ })).toBeNull();
  expect(screen.queryByRole('button', { name: 'Edit' })).toBeNull();
  expect(screen.queryByRole('button', { name: 'Restock' })).toBeNull();
});

it('lets an admin edit a vehicle and reloads the changed inventory', async () => {
  localStorage.setItem('token', 'valid-token');
  localStorage.setItem('role', 'admin');
  const updated = { ...vehicle, model: 'Corolla' };
  const fetch = vi.fn()
    .mockResolvedValueOnce(response([vehicle]))
    .mockResolvedValueOnce(response(updated))
    .mockResolvedValueOnce(response([updated]));
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  await screen.findByText('Toyota Camry');
  fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
  fireEvent.change(screen.getByLabelText('model', { selector: 'input' }), { target: { value: 'Corolla' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save vehicle' }));
  expect(await screen.findByText('Toyota Corolla')).toBeTruthy();
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/vehicles/1'), expect.objectContaining({ method: 'PUT' }));
});

it('lets an admin restock a vehicle', async () => {
  localStorage.setItem('token', 'valid-token');
  localStorage.setItem('role', 'admin');
  const fetch = vi.fn()
    .mockResolvedValueOnce(response([vehicle]))
    .mockResolvedValueOnce(response({ ...vehicle, quantity: 5 }))
    .mockResolvedValueOnce(response([{ ...vehicle, quantity: 5 }]));
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  await screen.findByText('Toyota Camry');
  fireEvent.click(screen.getByRole('button', { name: 'Restock' }));
  fireEvent.change(screen.getByLabelText('Restock quantity'), { target: { value: '3' } });
  fireEvent.click(screen.getByRole('button', { name: 'Add stock' }));
  expect(await screen.findByText('5 available')).toBeTruthy();
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/restock'), expect.objectContaining({ method: 'POST' }));
});

it('requires confirmation before an admin deletes a vehicle', async () => {
  localStorage.setItem('token', 'valid-token');
  localStorage.setItem('role', 'admin');
  const fetch = vi.fn()
    .mockResolvedValueOnce(response([vehicle]))
    .mockResolvedValueOnce(response(null, 204))
    .mockResolvedValueOnce(response([]));
  vi.stubGlobal('fetch', fetch);
  vi.spyOn(window, 'confirm').mockReturnValue(true);
  render(<App />);
  await screen.findByText('Toyota Camry');
  fireEvent.click(screen.getByRole('button', { name: 'Delete Toyota Camry' }));
  expect(await screen.findByText('No vehicles found. Add your first vehicle to get started.')).toBeTruthy();
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/vehicles/1'), expect.objectContaining({ method: 'DELETE' }));
});
