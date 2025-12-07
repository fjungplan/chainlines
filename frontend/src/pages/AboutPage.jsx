import './AboutPage.css';

export default function AboutPage() {
  return (
    <div className="about-page">
      <div className="about-container">
        <h1>About ChainLines</h1>
        
        <section>
          <h2>What is ChainLines?</h2>
          <p>
            ChainLines is an open-source platform dedicated to documenting and visualizing the history of professional cycling teams. 
            We track team lineages, mergers, splits, and transformations across the sport's rich history.
          </p>
        </section>

        <section>
          <h2>Our Mission</h2>
          <p>
            To create an accurate, comprehensive, and accessible record of professional cycling team histories, enabling fans, 
            researchers, and enthusiasts to understand the complex web of team relationships and evolution over time.
          </p>
        </section>

        <section>
          <h2>Community-Driven</h2>
          <p>
            ChainLines is built by the cycling community, for the cycling community. We believe in collaborative, transparent knowledge 
            sharing and welcome contributions from anyone passionate about cycling history.
          </p>
        </section>

        <section>
          <h2>Open Source</h2>
          <p>
            Our code and data are open source, allowing researchers, developers, and fans to contribute, fork, and build upon our work. 
            We're committed to maintaining transparency and accessibility in all aspects of the project.
          </p>
        </section>

        <section>
          <h2>Contact & Contribute</h2>
          <p>
            Interested in contributing? Have questions or corrections? We'd love to hear from you. Visit our GitHub repository or 
            reach out through our community channels.
          </p>
        </section>
      </div>
    </div>
  );
}
