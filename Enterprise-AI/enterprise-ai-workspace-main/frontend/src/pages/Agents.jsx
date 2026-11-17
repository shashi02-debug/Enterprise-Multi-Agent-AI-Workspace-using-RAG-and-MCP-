import "./Agents.css";

import { useState } from "react";

import {
  runAgentWorkflow,
} from "../services/api";


const agents = [
  {
    number: "01",
    icon: "✦",
    name: "Supervisor Agent",
    status: "Active",
    role: "Orchestration & Routing",
    description:
      "Analyzes the user's request and determines which agent or workflow should handle it.",
    capabilities: [
      "Intent detection",
      "Agent routing",
      "Workflow coordination",
    ],
  },

  {
    number: "02",
    icon: "⌕",
    name: "Knowledge Agent",
    status: "Active",
    role: "RAG & Knowledge Retrieval",
    description:
      "Retrieves relevant information from the enterprise knowledge base using semantic search.",
    capabilities: [
      "ChromaDB retrieval",
      "Semantic search",
      "Document grounding",
    ],
  },

  {
    number: "03",
    icon: "✧",
    name: "Response Agent",
    status: "Active",
    role: "Answer Generation",
    description:
      "Uses the retrieved context to generate a grounded, structured response for the user.",
    capabilities: [
      "Context-aware generation",
      "Markdown responses",
      "Source-aware answers",
    ],
  },
];


function Agents() {

  const [testQuery, setTestQuery] =
    useState(
      "summarize the accommodation booking document"
    );

  const [testing, setTesting] =
    useState(false);

  const [testResult, setTestResult] =
    useState(null);

  const [testError, setTestError] =
    useState("");


  const handleTestWorkflow =
    async () => {

      const query =
        testQuery.trim();

      if (
        !query ||
        testing
      ) {
        return;
      }


      setTesting(true);
      setTestResult(null);
      setTestError("");


      try {

        const data =
          await runAgentWorkflow(
            query
          );


        setTestResult(
          data
        );

      } catch (error) {

        console.error(
          "Agent workflow test failed:",
          error
        );

        setTestError(
          error?.message ||
            "Unable to execute the agent workflow."
        );

      } finally {

        setTesting(false);
      }
    };


  return (
    <div className="agents-page">

      {/* =================================================
          PAGE HERO
      ================================================= */}

      <section className="agents-hero">

        <div className="agents-badge">
          <span>✦</span>
          MULTI-AGENT SYSTEM
        </div>


        <h1>
          Intelligent agents,
          <br />
          <span>working together.</span>
        </h1>


        <p>
          Coordinate specialized AI agents through
          <br className="desktop-only" />
          an intelligent enterprise workflow.
        </p>

      </section>


      {/* =================================================
          AGENT STATUS
      ================================================= */}

      <section className="agents-section">

        <div className="agents-section-heading">

          <div>
            <h2>
              Active agents
            </h2>

            <p>
              Agents currently implemented
              in the workspace.
            </p>
          </div>


          <div className="agents-live-status">
            <span />
            3 agents active
          </div>

        </div>


        <div className="agents-grid">

          {agents.map(
            (agent) => (

              <article
                className="agent-card"
                key={agent.name}
              >

                <div className="agent-card-top">

                  <div className="agent-icon">
                    {agent.icon}
                  </div>


                  <span className="agent-number">
                    {agent.number}
                  </span>

                </div>


                <div className="agent-card-body">

                  <div className="agent-name-row">

                    <h3>
                      {agent.name}
                    </h3>


                    <span className="agent-status">
                      <span />
                      {agent.status}
                    </span>

                  </div>


                  <span className="agent-role">
                    {agent.role}
                  </span>


                  <p className="agent-description">
                    {agent.description}
                  </p>


                  <div className="agent-capabilities">

                    {agent.capabilities.map(
                      (capability) => (

                        <span
                          key={
                            capability
                          }
                        >
                          {capability}
                        </span>

                      )
                    )}

                  </div>

                </div>

              </article>

            )
          )}

        </div>

      </section>


      {/* =================================================
          WORKFLOW ARCHITECTURE
      ================================================= */}

      <section className="agents-section">

        <div className="agents-section-heading">

          <div>
            <h2>
              Agent workflow
            </h2>

            <p>
              Requests move through specialized
              agents before the final response is generated.
            </p>
          </div>

        </div>


        <div className="agent-flow">

          <div className="agent-flow-step">

            <div className="agent-flow-icon">
              👤
            </div>

            <strong>
              User
            </strong>

            <span>
              Request
            </span>

          </div>


          <div className="agent-flow-arrow">
            →
          </div>


          <div className="agent-flow-step">

            <div className="agent-flow-icon">
              ✦
            </div>

            <strong>
              Supervisor
            </strong>

            <span>
              Route
            </span>

          </div>


          <div className="agent-flow-arrow">
            →
          </div>


          <div className="agent-flow-step">

            <div className="agent-flow-icon">
              ⌕
            </div>

            <strong>
              Knowledge
            </strong>

            <span>
              Retrieve
            </span>

          </div>


          <div className="agent-flow-arrow">
            →
          </div>


          <div className="agent-flow-step">

            <div className="agent-flow-icon">
              ✧
            </div>

            <strong>
              Response
            </strong>

            <span>
              Generate
            </span>

          </div>

        </div>

      </section>


      {/* =================================================
          TEST WORKFLOW
      ================================================= */}

      <section className="agents-test-section">

        <div className="agents-test-header">

          <div>

            <span className="agents-test-label">
              LIVE WORKFLOW TEST
            </span>

            <h2>
              Test your multi-agent system
            </h2>

            <p>
              Send a real request through the
              implemented agent pipeline.
            </p>

          </div>

        </div>


        <div className="agents-test-box">

          <div className="agents-test-input-row">

            <input
              type="text"
              value={testQuery}
              onChange={(event) =>
                setTestQuery(
                  event.target.value
                )
              }
              onKeyDown={(event) => {

                if (
                  event.key ===
                  "Enter"
                ) {
                  event.preventDefault();

                  handleTestWorkflow();
                }

              }}
              placeholder="Enter a request for the agents..."
              disabled={testing}
            />


            <button
              type="button"
              onClick={
                handleTestWorkflow
              }
              disabled={
                testing ||
                !testQuery.trim()
              }
            >
              {testing
                ? "Running..."
                : "Run workflow →"}
            </button>

          </div>


          {testError && (

            <div className="agents-test-error">
              {testError}
            </div>

          )}


          {testResult && (

            <div className="agents-test-result">

              <div className="agents-result-header">

                <div>
                  <span>
                    WORKFLOW COMPLETED
                  </span>

                  <strong>
                    {testResult.route ||
                      "general"} route
                  </strong>
                </div>


                <div className="agents-result-success">
                  <span />
                  Success
                </div>

              </div>


              <div className="agents-result-flow">

                {(
                  testResult.agent_workflow ||
                  []
                ).map(
                  (
                    agent,
                    index
                  ) => (

                    <div
                      className="agents-result-step"
                      key={`${agent}-${index}`}
                    >

                      <span>
                        {index + 1}
                      </span>

                      <strong>
                        {agent}
                      </strong>

                      {index <
                        (
                          testResult
                            .agent_workflow ||
                          []
                        ).length -
                          1 && (
                        <b>
                          →
                        </b>
                      )}

                    </div>

                  )
                )}

              </div>


              <div className="agents-result-details">

                <div>
                  <span>
                    Retrieved chunks
                  </span>

                  <strong>
                    {
                      testResult.retrieved_chunks ??
                      0
                    }
                  </strong>
                </div>


                <div>
                  <span>
                    Sources
                  </span>

                  <strong>
                    {
                      testResult.sources
                        ?.length ??
                      0
                    }
                  </strong>
                </div>

              </div>


              {testResult.sources?.length >
                0 && (

                <div className="agents-result-sources">

                  <span>
                    Sources used
                  </span>

                  <div>

                    {testResult.sources.map(
                      (source) => (

                        <span
                          key={source}
                        >
                          📄 {source}
                        </span>

                      )
                    )}

                  </div>

                </div>

              )}

            </div>

          )}

        </div>

      </section>


      {/* =================================================
          FOOTER NOTE
      ================================================= */}

      <section className="agents-note">

        <div className="agents-note-icon">
          ✦
        </div>

        <div>

          <strong>
            Built with LangGraph orchestration
          </strong>

          <p>
            The supervisor coordinates specialized
            agents while RAG provides grounded
            enterprise knowledge.
          </p>

        </div>

      </section>

    </div>
  );
}


export default Agents;