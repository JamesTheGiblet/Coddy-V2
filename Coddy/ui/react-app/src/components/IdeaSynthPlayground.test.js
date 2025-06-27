// src/components/IdeaSynthPlayground.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import IdeaSynthPlayground from './IdeaSynthPlayground';

global.fetch = jest.fn();

describe('IdeaSynthPlayground', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders the form correctly', () => {
    render(<IdeaSynthPlayground />);
    expect(screen.getByRole('heading', { name: /idea synthesizer playground/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/base idea or problem/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/constraints/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/weird mode/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /synthesize ideas/i })).toBeInTheDocument();
  });

  // Now let's test the success case for form submission.
  test('handles successful form submission and displays results', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ideas: ['A fantastic new idea!', 'Another brilliant concept.'] }),
    });

    render(<IdeaSynthPlayground />);
    fireEvent.change(screen.getByLabelText(/base idea or problem/i), {
      target: { value: 'A new way to test React apps' },
    });
    fireEvent.click(screen.getByRole('button', { name: /synthesize ideas/i }));

    expect(screen.getByRole('button', { name: /generating.../i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('A fantastic new idea!')).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText('Another brilliant concept.')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: /generating.../i })).not.toBeInTheDocument();
  });

  test('handles API error and displays an error message', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: 'Something went wrong on the server!' }),
    });

    render(<IdeaSynthPlayground />);
    fireEvent.change(screen.getByLabelText(/base idea or problem/i), {
      target: { value: 'A failing test case' },
    });
    fireEvent.click(screen.getByRole('button', { name: /synthesize ideas/i }));

    await waitFor(() => {
      expect(screen.getByText('Something went wrong on the server!')).toBeInTheDocument();
    });

    expect(screen.queryByText(/a fantastic new idea/i)).not.toBeInTheDocument();
  });
});
