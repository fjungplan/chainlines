import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import TimelineEventItem from '../../../src/components/teams/TimelineEventItem';

const renderComponent = (props) => {
    return render(
        <BrowserRouter>
            <TimelineEventItem {...props} />
        </BrowserRouter>
    );
};

describe('TimelineEventItem', () => {
    it('renders MERGE INCOMING correctly', () => {
        const event = {
            event_type: 'MERGE',
            year: 2024,
            direction: 'INCOMING',
            related_team_name: 'Team A',
            related_team_id: '123'
        };
        renderComponent({ event });
        expect(screen.getByText('Merged from')).toBeInTheDocument();
        expect(screen.getByText('Team A')).toBeInTheDocument();
        expect(screen.getByTitle('MERGE')).toBeInTheDocument();
    });

    it('renders MERGE OUTGOING correctly', () => {
        const event = {
            event_type: 'MERGE',
            year: 2024,
            direction: 'OUTGOING',
            related_team_name: 'Team B',
            related_team_id: '456'
        };
        renderComponent({ event });
        expect(screen.getByText('Merged into')).toBeInTheDocument();
        expect(screen.getByTitle('MERGE')).toBeInTheDocument();
    });

    it('renders SPLIT INCOMING correctly', () => {
        const event = {
            event_type: 'SPLIT',
            year: 2024,
            direction: 'INCOMING',
            related_team_name: 'Team C'
        };
        renderComponent({ event });
        expect(screen.getByText('Split from')).toBeInTheDocument();
        expect(screen.getByTitle('SPLIT')).toBeInTheDocument();
    });

    it('renders SPLIT OUTGOING correctly', () => {
        const event = {
            event_type: 'SPLIT',
            year: 2024,
            direction: 'OUTGOING',
            related_team_name: 'Team D'
        };
        renderComponent({ event });
        expect(screen.getByText('Split to')).toBeInTheDocument();
    });

    it('renders LEGAL_TRANSFER correctly', () => {
        const event = {
            event_type: 'LEGAL_TRANSFER',
            year: 2024,
            direction: 'INCOMING',
            related_team_name: 'Team E'
        };
        renderComponent({ event });
        expect(screen.getByText('Legal transfer from')).toBeInTheDocument();
        expect(screen.getByTitle('LEGAL_TRANSFER')).toBeInTheDocument();
    });

    it('renders SPIRITUAL_SUCCESSION correctly', () => {
        const event = {
            event_type: 'SPIRITUAL_SUCCESSION',
            year: 2024,
            direction: 'INCOMING',
            related_team_name: 'Team F'
        };
        renderComponent({ event });
        expect(screen.getByText('Spiritual successor of')).toBeInTheDocument();
        expect(screen.getByTitle('SPIRITUAL_SUCCESSION')).toBeInTheDocument();
    });

    it('renders default generic event for unknown type', () => {
        const event = {
            event_type: 'UNKNOWN_TYPE',
            year: 2024,
            related_team_name: 'Team Z'
        };
        renderComponent({ event });
        expect(screen.getByText('Event')).toBeInTheDocument();
        expect(screen.getByTitle('UNKNOWN_TYPE')).toBeInTheDocument();
    });
});
