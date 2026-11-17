import "./Tasks.css";

import { useState } from "react";


// =====================================================
// TASKS PAGE
// =====================================================

function Tasks() {

  // ===================================================
  // DEMO TASKS
  // ===================================================

  const [tasks, setTasks] = useState([
    {
      id: 1,
      name: "Daily Project Email Summary",
      description:
        "Check Gmail for important project-related emails and prepare a concise summary.",
      services: ["Gmail"],
      schedule: "Every day",
      time: "09:00 AM",
      active: true,
      status: "Ready",
      lastRun: "Not run yet",
    },
    {
      id: 2,
      name: "Project Document Monitor",
      description:
        "Check Google Drive for newly uploaded project documents and summarize them.",
      services: ["Google Drive"],
      schedule: "Every day",
      time: "06:00 PM",
      active: true,
      status: "Ready",
      lastRun: "Not run yet",
    },
  ]);


  // ===================================================
  // CREATE TASK MODAL
  // ===================================================

  const [showCreateTask, setShowCreateTask] =
    useState(false);

  const [taskName, setTaskName] =
    useState("");

  const [taskDescription, setTaskDescription] =
    useState("");

  const [schedule, setSchedule] =
    useState("Every day");

  const [taskTime, setTaskTime] =
    useState("09:00");

  const [selectedServices, setSelectedServices] =
    useState(["Gmail"]);


  // ===================================================
  // HELPERS
  // ===================================================

  const formatTime = (time) => {
    if (!time) return "";

    const [hours, minutes] =
      time.split(":");

    let hour =
      parseInt(hours, 10);

    const suffix =
      hour >= 12
        ? "PM"
        : "AM";

    hour =
      hour % 12 || 12;

    return `${hour}:${minutes} ${suffix}`;
  };


  const serviceIcon = (service) => {
    if (service === "Gmail") return "✉";
    if (service === "Google Drive") return "▣";
    if (service === "Google Calendar") return "◫";
    return "✦";
  };


  const toggleService = (service) => {
    setSelectedServices((current) =>
      current.includes(service)
        ? current.filter(
            (item) => item !== service
          )
        : [...current, service]
    );
  };


  // ===================================================
  // CREATE TASK
  // ===================================================

  const handleCreateTask = () => {
    if (!taskName.trim()) return;

    const newTask = {
      id: Date.now(),
      name: taskName.trim(),
      description:
        taskDescription.trim() ||
        "No task description provided.",
      services:
        selectedServices.length
          ? selectedServices
          : ["AI"],
      schedule,
      time: formatTime(taskTime),
      active: true,
      status: "Ready",
      lastRun: "Not run yet",
    };

    setTasks((current) => [
      newTask,
      ...current,
    ]);

    setTaskName("");
    setTaskDescription("");
    setSchedule("Every day");
    setTaskTime("09:00");
    setSelectedServices(["Gmail"]);
    setShowCreateTask(false);
  };


  // ===================================================
  // TASK CONTROLS
  // ===================================================

  const toggleTask = (id) => {
    setTasks((current) =>
      current.map((task) =>
        task.id === id
          ? {
              ...task,
              active: !task.active,
              status:
                !task.active
                  ? "Ready"
                  : "Paused",
            }
          : task
      )
    );
  };


  const runTask = (id) => {
    setTasks((current) =>
      current.map((task) =>
        task.id === id
          ? {
              ...task,
              status: "Queued",
              lastRun: "Just now",
            }
          : task
      )
    );

    setTimeout(() => {
      setTasks((current) =>
        current.map((task) =>
          task.id === id
            ? {
                ...task,
                status: "Completed",
              }
            : task
        )
      );
    }, 1200);
  };


  const deleteTask = (id) => {
    setTasks((current) =>
      current.filter(
        (task) => task.id !== id
      )
    );
  };


  // ===================================================
  // STYLES
  // ===================================================

  const styles = {
    page: {
      maxWidth: "1160px",
      margin: "0 auto",
      padding: "34px 30px 70px",
    },

    badge: {
      display: "inline-flex",
      alignItems: "center",
      gap: "8px",
      padding: "7px 12px",
      border: "1px solid #e5dcff",
      borderRadius: "999px",
      background: "#faf8ff",
      color: "#6941e8",
      fontSize: "11px",
      fontWeight: "800",
      letterSpacing: "0.06em",
    },

    title: {
      margin: "14px 0 7px",
      fontSize: "38px",
      lineHeight: "1.08",
      fontWeight: "800",
      color: "#171426",
    },

    subtitle: {
      margin: 0,
      maxWidth: "650px",
      color: "#81798f",
      fontSize: "14px",
      lineHeight: "1.6",
    },

    primaryButton: {
      border: "none",
      borderRadius: "11px",
      padding: "12px 17px",
      background: "#6941e8",
      color: "#ffffff",
      fontWeight: "750",
      fontSize: "13px",
      cursor: "pointer",
      boxShadow:
        "0 8px 20px rgba(105,65,232,0.18)",
      whiteSpace: "nowrap",
    },

    statCard: {
      background: "#ffffff",
      border: "1px solid #ebe6f4",
      borderRadius: "15px",
      padding: "17px",
      display: "flex",
      alignItems: "center",
      gap: "12px",
      boxShadow:
        "0 5px 18px rgba(53,34,95,0.035)",
    },

    statIcon: {
      width: "38px",
      height: "38px",
      borderRadius: "11px",
      display: "grid",
      placeItems: "center",
      background: "#f1edff",
      color: "#6941e8",
      fontWeight: "800",
      flexShrink: 0,
    },

    sectionTitle: {
      margin: 0,
      fontSize: "18px",
      fontWeight: "750",
      color: "#241d34",
    },

    sectionText: {
      margin: "4px 0 0",
      color: "#8b8498",
      fontSize: "12px",
    },

    taskCard: {
      background: "#ffffff",
      border: "1px solid #ebe6f4",
      borderRadius: "15px",
      padding: "18px",
      boxShadow:
        "0 5px 18px rgba(53,34,95,0.035)",
    },

    servicePill: {
      display: "inline-flex",
      alignItems: "center",
      gap: "5px",
      padding: "5px 9px",
      borderRadius: "7px",
      background: "#f8f6fc",
      border: "1px solid #eeeaf5",
      color: "#625b70",
      fontSize: "10px",
      fontWeight: "700",
    },

    fieldLabel: {
      display: "block",
      width: "100%",
      marginBottom: "7px",
      color: "#40394e",
      fontSize: "12px",
      lineHeight: "1.3",
      fontWeight: "750",
    },

    field: {
      display: "block",
      width: "100%",
      boxSizing: "border-box",
      padding: "11px 12px",
      border: "1px solid #ded7eb",
      borderRadius: "9px",
      background: "#ffffff",
      color: "#292332",
      fontFamily: "inherit",
      fontSize: "13px",
      outline: "none",
    },
  };


  // ===================================================
  // RENDER
  // ===================================================

  return (
    <div style={styles.page}>

      {/* =============================================
          PAGE HEADER
      ============================================= */}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          gap: "20px",
          marginBottom: "28px",
        }}
      >

        <div>

          <div style={styles.badge}>
            <span>✦</span>
            ENTERPRISE AI WORKSPACE
          </div>

          <h2 style={styles.title}>
            AI Tasks
          </h2>

          <p style={styles.subtitle}>
            Automate repetitive enterprise
            workflows with intelligent AI agents.
          </p>

        </div>


        <button
          type="button"
          onClick={() =>
            setShowCreateTask(true)
          }
          style={styles.primaryButton}
        >
          + Create Task
        </button>

      </div>


      {/* =============================================
          STATISTICS
      ============================================= */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(3, minmax(0, 1fr))",
          gap: "14px",
          marginBottom: "30px",
        }}
      >

        <div style={styles.statCard}>
          <div style={styles.statIcon}>
            ✦
          </div>

          <div>
            <div
              style={{
                fontSize: "20px",
                fontWeight: "800",
                color: "#211b32",
              }}
            >
              {
                tasks.filter(
                  (task) => task.active
                ).length
              }
            </div>

            <div
              style={{
                marginTop: "2px",
                fontSize: "11px",
                color: "#8b8498",
              }}
            >
              Active Tasks
            </div>
          </div>
        </div>


        <div style={styles.statCard}>
          <div style={styles.statIcon}>
            ✓
          </div>

          <div>
            <div
              style={{
                fontSize: "20px",
                fontWeight: "800",
                color: "#211b32",
              }}
            >
              {
                tasks.filter(
                  (task) =>
                    task.status ===
                    "Completed"
                ).length
              }
            </div>

            <div
              style={{
                marginTop: "2px",
                fontSize: "11px",
                color: "#8b8498",
              }}
            >
              Completed
            </div>
          </div>
        </div>


        <div style={styles.statCard}>
          <div style={styles.statIcon}>
            ⚡
          </div>

          <div>
            <div
              style={{
                fontSize: "20px",
                fontWeight: "800",
                color: "#211b32",
              }}
            >
              {tasks.length}
            </div>

            <div
              style={{
                marginTop: "2px",
                fontSize: "11px",
                color: "#8b8498",
              }}
            >
              Total Tasks
            </div>
          </div>
        </div>

      </div>


      {/* =============================================
          TASK SECTION
      ============================================= */}

      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          marginBottom: "13px",
        }}
      >

        <div>
          <h3 style={styles.sectionTitle}>
            Your Tasks
          </h3>

          <p style={styles.sectionText}>
            Manage automated AI workflows.
          </p>
        </div>

      </div>


      {/* =============================================
          TASK CARDS
      ============================================= */}

      <div
        style={{
          display: "grid",
          gap: "12px",
        }}
      >

        {tasks.map((task) => (

          <div
            key={task.id}
            style={styles.taskCard}
          >

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "20px",
              }}
            >

              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  minWidth: 0,
                  flex: 1,
                }}
              >

                <div
                  style={{
                    width: "38px",
                    height: "38px",
                    borderRadius: "11px",
                    display: "grid",
                    placeItems: "center",
                    background: "#f1edff",
                    color: "#6941e8",
                    fontWeight: "800",
                    flexShrink: 0,
                  }}
                >
                  ✦
                </div>


                <div style={{ minWidth: 0 }}>

                  <div
                    style={{
                      fontSize: "15px",
                      fontWeight: "750",
                      color: "#241d34",
                    }}
                  >
                    {task.name}
                  </div>

                  <div
                    style={{
                      marginTop: "4px",
                      color: "#8a8398",
                      fontSize: "11px",
                    }}
                  >
                    {task.schedule}
                    {" • "}
                    {task.time}
                  </div>

                  <p
                    style={{
                      margin: "10px 0 10px",
                      color: "#716a7e",
                      fontSize: "12px",
                      lineHeight: "1.55",
                    }}
                  >
                    {task.description}
                  </p>


                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "6px",
                    }}
                  >
                    {task.services.map(
                      (service) => (
                        <span
                          key={service}
                          style={styles.servicePill}
                        >
                          {serviceIcon(
                            service
                          )}
                          {service}
                        </span>
                      )
                    )}
                  </div>

                </div>

              </div>


              {/* CONTROLS */}

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-end",
                  gap: "17px",
                  flexShrink: 0,
                }}
              >

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "9px",
                  }}
                >

                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: "750",
                      color:
                        task.status ===
                        "Completed"
                          ? "#16865f"
                          : task.active
                          ? "#6941e8"
                          : "#91899d",
                    }}
                  >
                    {task.status}
                  </span>


                  <button
                    type="button"
                    onClick={() =>
                      toggleTask(
                        task.id
                      )
                    }
                    aria-label={
                      task.active
                        ? "Pause task"
                        : "Activate task"
                    }
                    style={{
                      width: "40px",
                      height: "22px",
                      padding: 0,
                      border: "none",
                      borderRadius: "999px",
                      background:
                        task.active
                          ? "#6941e8"
                          : "#d8d2e2",
                      position: "relative",
                      cursor: "pointer",
                    }}
                  >
                    <span
                      style={{
                        position: "absolute",
                        top: "3px",
                        left:
                          task.active
                            ? "21px"
                            : "3px",
                        width: "16px",
                        height: "16px",
                        borderRadius: "50%",
                        background: "#ffffff",
                        transition:
                          "left 0.2s ease",
                      }}
                    />
                  </button>

                </div>


                <div
                  style={{
                    display: "flex",
                    gap: "6px",
                  }}
                >

                  <button
                    type="button"
                    onClick={() =>
                      runTask(
                        task.id
                      )
                    }
                    disabled={
                      !task.active ||
                      task.status ===
                        "Queued"
                    }
                    style={{
                      border:
                        "1px solid #ddd5f0",
                      background: "#ffffff",
                      color: "#6941e8",
                      borderRadius: "8px",
                      padding:
                        "7px 10px",
                      fontSize: "10px",
                      fontWeight: "750",
                      cursor: "pointer",
                      opacity:
                        !task.active
                          ? 0.5
                          : 1,
                    }}
                  >
                    Run now
                  </button>


                  <button
                    type="button"
                    onClick={() =>
                      deleteTask(
                        task.id
                      )
                    }
                    style={{
                      border:
                        "1px solid #f0dfe5",
                      background: "#fffafb",
                      color: "#b04d67",
                      borderRadius: "8px",
                      padding:
                        "7px 10px",
                      fontSize: "10px",
                      fontWeight: "750",
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>

                </div>

              </div>

            </div>


            <div
              style={{
                borderTop:
                  "1px solid #f0ecf5",
                marginTop: "15px",
                paddingTop: "10px",
                fontSize: "10px",
                color: "#928a9f",
              }}
            >
              Last execution:{" "}
              <strong
                style={{
                  color: "#6e667b",
                }}
              >
                {task.lastRun}
              </strong>
            </div>

          </div>

        ))}

      </div>


      {/* =============================================
          CREATE TASK MODAL
      ============================================= */}

      {showCreateTask && (

        <div
          onClick={() =>
            setShowCreateTask(false)
          }
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            background:
              "rgba(24,18,42,0.42)",
            backdropFilter:
              "blur(4px)",
          }}
        >

          <div
            onClick={(event) =>
              event.stopPropagation()
            }
            style={{
              width: "100%",
              maxWidth: "590px",
              maxHeight: "calc(100vh - 48px)",
              overflowY: "auto",
              background: "#ffffff",
              border:
                "1px solid rgba(226,219,239,0.9)",
              borderRadius: "20px",
              boxShadow:
                "0 28px 80px rgba(31,20,60,0.24)",
            }}
          >

            {/* MODAL HEADER */}

            <div
              style={{
                padding:
                  "23px 25px 19px",
                borderBottom:
                  "1px solid #f0ecf5",
                display: "flex",
                justifyContent:
                  "space-between",
                alignItems: "flex-start",
                gap: "15px",
              }}
            >

              <div>

                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "7px",
                    color: "#6941e8",
                    fontSize: "10px",
                    fontWeight: "800",
                    letterSpacing:
                      "0.05em",
                    marginBottom: "7px",
                  }}
                >
                  <span>✦</span>
                  AI AUTOMATION
                </div>

                <h3
                  style={{
                    margin: 0,
                    fontSize: "21px",
                    lineHeight: "1.2",
                    fontWeight: "800",
                    color: "#211b32",
                  }}
                >
                  Create AI Task
                </h3>

                <p
                  style={{
                    margin:
                      "5px 0 0",
                    fontSize: "12px",
                    lineHeight: "1.5",
                    color: "#8a8399",
                  }}
                >
                  Define a workflow for your AI agents.
                </p>

              </div>


              <button
                type="button"
                onClick={() =>
                  setShowCreateTask(
                    false
                  )
                }
                aria-label="Close"
                style={{
                  width: "32px",
                  height: "32px",
                  border: "none",
                  borderRadius: "50%",
                  background: "#f6f3fa",
                  color: "#70687e",
                  cursor: "pointer",
                  fontSize: "17px",
                  flexShrink: 0,
                }}
              >
                ×
              </button>

            </div>


            {/* MODAL BODY */}

            <div
              style={{
                padding:
                  "22px 25px 24px",
              }}
            >

              {/* TASK NAME */}

              <div
                style={{
                  marginBottom: "17px",
                }}
              >

                <label style={styles.fieldLabel}>
                  Task name
                </label>

                <input
                  type="text"
                  value={taskName}
                  onChange={(event) =>
                    setTaskName(
                      event.target.value
                    )
                  }
                  placeholder="e.g. Daily Project Email Summary"
                  style={styles.field}
                />

              </div>


              {/* DESCRIPTION */}

              <div
                style={{
                  marginBottom: "19px",
                }}
              >

                <label style={styles.fieldLabel}>
                  What should the AI do?
                </label>

                <textarea
                  value={taskDescription}
                  onChange={(event) =>
                    setTaskDescription(
                      event.target.value
                    )
                  }
                  placeholder="Describe the workflow in natural language..."
                  rows={4}
                  style={{
                    ...styles.field,
                    resize: "vertical",
                    minHeight: "92px",
                    lineHeight: "1.5",
                  }}
                />

              </div>


              {/* SERVICES */}

              <div
                style={{
                  marginBottom: "19px",
                }}
              >

                <label style={styles.fieldLabel}>
                  Connected services
                </label>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "repeat(3, 1fr)",
                    gap: "9px",
                  }}
                >

                  {[
                    "Gmail",
                    "Google Drive",
                    "Google Calendar",
                  ].map((service) => {

                    const selected =
                      selectedServices.includes(
                        service
                      );

                    return (
                      <button
                        key={service}
                        type="button"
                        onClick={() =>
                          toggleService(
                            service
                          )
                        }
                        style={{
                          display: "flex",
                          alignItems:
                            "center",
                          justifyContent:
                            "center",
                          gap: "6px",
                          minHeight: "45px",
                          border:
                            selected
                              ? "1px solid #8d72ed"
                              : "1px solid #e3deec",
                          borderRadius:
                            "10px",
                          background:
                            selected
                              ? "#f5f1ff"
                              : "#ffffff",
                          color:
                            selected
                              ? "#6941e8"
                              : "#6f687c",
                          cursor: "pointer",
                          fontSize: "11px",
                          fontWeight: "700",
                        }}
                      >
                        <span>
                          {selected
                            ? "✓"
                            : serviceIcon(
                                service
                              )}
                        </span>

                        {service}

                      </button>
                    );
                  })}

                </div>

              </div>


              {/* SCHEDULE */}

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "1fr 1fr",
                  gap: "13px",
                }}
              >

                <div>

                  <label style={styles.fieldLabel}>
                    Schedule
                  </label>

                  <select
                    value={schedule}
                    onChange={(event) =>
                      setSchedule(
                        event.target.value
                      )
                    }
                    style={{
                      ...styles.field,
                      cursor: "pointer",
                    }}
                  >
                    <option>
                      Every day
                    </option>
                    <option>
                      Every week
                    </option>
                    <option>
                      Every month
                    </option>
                    <option>
                      Once
                    </option>
                  </select>

                </div>


                <div>

                  <label style={styles.fieldLabel}>
                    Time
                  </label>

                  <input
                    type="time"
                    value={taskTime}
                    onChange={(event) =>
                      setTaskTime(
                        event.target.value
                      )
                    }
                    style={{
                      ...styles.field,
                      cursor: "pointer",
                    }}
                  />

                </div>

              </div>

            </div>


            {/* MODAL FOOTER */}

            <div
              style={{
                padding:
                  "15px 25px",
                borderTop:
                  "1px solid #f0ecf5",
                background:
                  "#fcfbfe",
                display: "flex",
                justifyContent:
                  "flex-end",
                gap: "9px",
              }}
            >

              <button
                type="button"
                onClick={() =>
                  setShowCreateTask(
                    false
                  )
                }
                style={{
                  border:
                    "1px solid #ded7e9",
                  background:
                    "#ffffff",
                  color:
                    "#655e72",
                  borderRadius:
                    "9px",
                  padding:
                    "10px 16px",
                  fontSize: "12px",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>


              <button
                type="button"
                onClick={
                  handleCreateTask
                }
                disabled={
                  !taskName.trim()
                }
                style={{
                  border: "none",
                  background:
                    "#6941e8",
                  color:
                    "#ffffff",
                  borderRadius:
                    "9px",
                  padding:
                    "10px 18px",
                  fontSize: "12px",
                  fontWeight: "750",
                  cursor: "pointer",
                  opacity:
                    taskName.trim()
                      ? 1
                      : 0.5,
                }}
              >
                Create Task
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}


export default Tasks;
