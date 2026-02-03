import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import NumberField from '../../../../src/components/admin/fields/NumberField';
import SliderField from '../../../../src/components/admin/fields/SliderField';
import ToggleField from '../../../../src/components/admin/fields/ToggleField';
import InfoTooltip from '../../../../src/components/admin/fields/InfoTooltip';

describe('NumberField', () => {
    it('renders label and input', () => {
        render(
            <NumberField
                label="Population Size"
                value={1000}
                onChange={() => { }}
            />
        );
        expect(screen.getByText('Population Size')).toBeInTheDocument();
        expect(screen.getByRole('spinbutton')).toHaveValue(1000);
    });

    it('calls onChange with valid number', () => {
        const handleChange = vi.fn();
        render(
            <NumberField
                label="Test"
                value={100}
                onChange={handleChange}
            />
        );

        const input = screen.getByRole('spinbutton');
        fireEvent.change(input, { target: { value: '200' } });
        expect(handleChange).toHaveBeenCalledWith(200);
    });

    it('enforces min/max constraints', () => {
        render(
            <NumberField
                label="Test"
                value={50}
                min={0}
                max={100}
                onChange={() => { }}
            />
        );

        const input = screen.getByRole('spinbutton');
        expect(input).toHaveAttribute('min', '0');
        expect(input).toHaveAttribute('max', '100');
    });

    it('displays tooltip when provided', () => {
        render(
            <NumberField
                label="Test"
                value={100}
                tooltip="This is a helpful tip"
                onChange={() => { }}
            />
        );

        expect(screen.getByTitle('This is a helpful tip')).toBeInTheDocument();
    });
});

describe('SliderField', () => {
    it('renders label, slider, and value display', () => {
        render(
            <SliderField
                label="Mutation Rate"
                value={0.2}
                min={0}
                max={1}
                step={0.01}
                onChange={() => { }}
            />
        );

        expect(screen.getByText('Mutation Rate')).toBeInTheDocument();
        expect(screen.getByRole('slider')).toHaveValue('0.2');
        expect(screen.getByText('0.20')).toBeInTheDocument(); // Value display
    });

    it('calls onChange with parsed number', () => {
        const handleChange = vi.fn();
        render(
            <SliderField
                label="Test"
                value={0.5}
                min={0}
                max={1}
                step={0.1}
                onChange={handleChange}
            />
        );

        const slider = screen.getByRole('slider');
        fireEvent.change(slider, { target: { value: '0.8' } });
        expect(handleChange).toHaveBeenCalledWith(0.8);
    });
});

describe('ToggleField', () => {
    it('renders label and checkbox', () => {
        render(
            <ToggleField
                label="Enable Scoreboard"
                value={true}
                onChange={() => { }}
            />
        );

        expect(screen.getByText('Enable Scoreboard')).toBeInTheDocument();
        expect(screen.getByRole('checkbox')).toBeChecked();
    });

    it('toggles value on click', () => {
        const handleChange = vi.fn();
        render(
            <ToggleField
                label="Test"
                value={false}
                onChange={handleChange}
            />
        );

        const checkbox = screen.getByRole('checkbox');
        fireEvent.click(checkbox);
        expect(handleChange).toHaveBeenCalledWith(true);
    });
});

describe('InfoTooltip', () => {
    it('renders info icon', () => {
        render(<InfoTooltip content="Helpful information" />);
        expect(screen.getByText('ⓘ')).toBeInTheDocument();
    });

    it('displays tooltip on hover', async () => {
        render(<InfoTooltip content="Helpful information" />);

        const icon = screen.getByText('ⓘ');
        fireEvent.mouseEnter(icon);

        expect(screen.getByText('Helpful information')).toBeInTheDocument();
    });
});
