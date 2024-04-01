import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AppRoute } from "./components/Routes/AppRoute";

import "@luxonis/theme/styles.css";
import "./App.css";

export const App = () => {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="app/:perceptionAppId" element={<Layout />}>
            <Route index element={<AppRoute />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
};
