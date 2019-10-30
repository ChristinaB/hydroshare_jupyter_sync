import React from 'react';
import ReactDOM from 'react-dom';
import './styles/App.scss';
import App from './containers/App';
import { Provider } from 'react-redux';
import setupStore from './redux/setup-store';
import * as serviceWorker from './serviceWorker';

const store = setupStore();

ReactDOM.render(
  <Provider store={store}>
    <App />
  </Provider>,
  document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
