import React, { useState, useEffect } from 'react';
import axios from 'axios';
import styles from './App.module.css';

const LoginForm = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('participant');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      alert('Пароли не совпадают!');
      return;
    }
    onLogin({ username, password, role });
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Логин" />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Пароль" />
      <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Подтвердите пароль" />
      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="participant">Участник</option>
        <option value="registrar">Регистратор</option>
      </select>
      <button type="submit">Войти</button>
    </form>
  );
};

const Bracket = ({ teams }) => {
  return (
    <div className={styles.bracket}>
      {teams.map((team, index) => (
        <div key={index}>{team}</div>
      ))}
    </div>
  );
};

const CompetitionsTable = ({ competitions }) => {
  return (
    <table className={styles.table}>
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Sport</th>
          <th>Date</th>
          <th>Participants Count</th>
          <th>Image</th>
        </tr>
      </thead>
      <tbody>
        {competitions.map((competition) => (
          <tr key={competition.id}>
            <td>{competition.id}</td>
            <td>{competition.title}</td>
            <td>{competition.sport}</td>
            <td>{competition.date}</td>
            <td>{competition.participantsCount}</td>
            <td><img src={competition.image} alt={competition.title} style={{ width: '50px', height: '50px' }} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const App = () => {
  const [user, setUser] = useState(null);
  const [competitions, setCompetitions] = useState([]);
  const teams = ['Team A', 'Team B', 'Team C', 'Team D'];

  useEffect(() => {
    const fetchCompetitions = async () => {
      try {
        const response = await axios.get('http://RETRACTED/api/competitions');
        setCompetitions(response.data);
      } catch (error) {
        console.error('Ошибка при получении данных о соревнованиях:', error);
      }
    };

    fetchCompetitions();
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>MatchUp</h1>
      {user ? (
        <div>
          {user.role === 'registrar' && (
            <div className={styles.adminSection}>
              <button id="create-tournament" onClick={() => alert('Создать турнир')}>Создать турнир</button>
              <div id="my-tournaments">Мои турниры</div>
              <div id="planning">Планирование</div>
            </div>
          )}
          {user.role === 'participant' && <Bracket teams={teams} />}
          <CompetitionsTable competitions={competitions} />
        </div>
      ) : (
        <LoginForm onLogin={handleLogin} />
      )}
    </div>
  );
};

export default App;
