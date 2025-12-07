import './ImprintPage.css';

export default function ImprintPage() {
  const currentYear = new Date().getFullYear();

  return (
    <div className="imprint-page">
      <div className="imprint-container">
        <h1>Legal Information / Imprint</h1>
        
        <section>
          <h2>Copyright Notice</h2>
          <p>
            &copy; 2025 - {currentYear} ChainLines. All rights reserved.
          </p>
          <p>
            ChainLines is an open-source project. The source code is made available under an open-source license. 
            Please refer to the LICENSE file in our repository for details.
          </p>
        </section>

        <section>
          <h2>Disclaimer</h2>
          <p>
            ChainLines is provided on an "as-is" basis. While we strive for accuracy, we make no warranties regarding the 
            completeness or accuracy of the information contained herein. Users are encouraged to verify information independently.
          </p>
          <p>
            ChainLines is not officially affiliated with any cycling teams, organizations, or governing bodies. All team names, 
            logos, and related data are used for informational and historical documentation purposes.
          </p>
        </section>

        <section>
          <h2>Limitation of Liability</h2>
          <p>
            In no event shall ChainLines or its contributors be liable for any indirect, incidental, special, consequential, or 
            punitive damages arising from your use or inability to use this service.
          </p>
        </section>

        <section>
          <h2>Data Privacy</h2>
          <p>
            ChainLines respects your privacy. If you have an account, we collect only the information necessary for authentication 
            and to track your contributions. We do not sell or share personal data with third parties.
          </p>
        </section>

        <section>
          <h2>User Contributions</h2>
          <p>
            By submitting data or edits to ChainLines, you grant us the right to use, modify, and distribute your contributions 
            under the same open-source license that governs the project.
          </p>
        </section>

        <section>
          <h2>Contact</h2>
          <p>
            For legal inquiries, privacy concerns, or other matters, please reach out through our community channels or 
            GitHub repository.
          </p>
        </section>
      </div>
    </div>
  );
}
