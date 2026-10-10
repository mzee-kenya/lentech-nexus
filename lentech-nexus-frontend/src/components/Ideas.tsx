import { Link } from 'react-router-dom'
import './Ideas.css'
function Ideas() {
  return (
    <section className="ideas">
      <h2>Ideas That Can Become Solutions</h2>

      <p>
        Share your ideas, discover opportunities, and connect with people
        who can help bring them to life.
      </p>

      <Link to="/ideas/new" className="ideas-cta">Share an Idea</Link>
    </section>
  )
}

export default Ideas