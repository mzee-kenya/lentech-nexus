import { Link } from 'react-router-dom'
import './CTA.css'

function CTA() {
  return (
    <section className="cta">
      <div className="cta-content">
        <h2>Have an Idea? Let's Build It.</h2>

        <p>
          Share your idea, connect with talented developers, and turn
          your vision into a real solution.
        </p>

        <div className="cta-actions">
          <Link to="/ideas/new" className="cta-button">Share an Idea</Link>
          <Link to="/projects" className="cta-button secondary">Explore Projects</Link>
        </div>
      </div>
    </section>
  )
}
export default CTA