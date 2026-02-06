import React from 'react';
import CenteredPageLayout from '../components/layout/CenteredPageLayout';
import Card from '../components/common/Card';
import './AboutPage.css'; // Reuse AboutPage styles for consistency

export default function ChangeLogPage() {
    return (
        <CenteredPageLayout>
            <Card title="Project Change Log">
                <section>
                    <h2>v0.9.3 (February 2026)</h2>
                    <p><strong>Current Version</strong></p>
                    <ul>
                        <li>Implemented Multi-Profile Optimizer (A/B/C configurations)</li>
                        <li>Enhanced line crossing optimization in layout algorithm</li>
                        <li>Resolved "ghost family" redundancy in database mergers</li>
                        <li>Added versioning transparency and dedicated project change log</li>
                    </ul>
                </section>

                <section>
                    <h2>Earlier Milestones</h2>
                    <p>
                        The project has evolved from an initial concept of tracking team successions to a
                        high-fidelity historical "river" visualization with automated structural discovery.
                    </p>
                    <ul>
                        <li>Smart Scraper (Phases 1-3) with structural heuristics</li>
                        <li>D3.js interactive timeline with jersey slice rendering</li>
                        <li>Audit-log based collaborative editing system</li>
                        <li>Production-ready Docker environment</li>
                    </ul>
                </section>
            </Card>
        </CenteredPageLayout>
    );
}
