import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

class DatabaseService {
  /**
   * Get a list of all available databases
   * @returns {Promise} Promise with the list of databases
   */
  async listDatabases() {
    try {
      const response = await axios.get(`${API_URL}/databases`);
      return response.data;
    } catch (error) {
      console.error('Error listing databases:', error);
      throw error;
    }
  }

  /**
   * Create a new database
   * @param {string} name - The name of the database
   * @param {boolean} withSampleData - Whether to include sample data
   * @returns {Promise} Promise with the result
   */
  async createDatabase(name, withSampleData = true) {
    try {
      const response = await axios.post(`${API_URL}/databases/create`, {
        name,
        with_sample_data: withSampleData
      });
      return response.data;
    } catch (error) {
      console.error('Error creating database:', error);
      throw error;
    }
  }

  /**
   * Select a database to use
   * @param {string} name - The name of the database
   * @returns {Promise} Promise with the result
   */
  async selectDatabase(name) {
    try {
      const response = await axios.post(`${API_URL}/databases/select`, {
        name
      });
      return response.data;
    } catch (error) {
      console.error('Error selecting database:', error);
      throw error;
    }
  }

  /**
   * Delete a database
   * @param {string} name - The name of the database
   * @returns {Promise} Promise with the result
   */
  async deleteDatabase(name) {
    try {
      const response = await axios.post(`${API_URL}/databases/delete`, {
        name
      });
      return response.data;
    } catch (error) {
      console.error('Error deleting database:', error);
      throw error;
    }
  }
}

export default new DatabaseService();
