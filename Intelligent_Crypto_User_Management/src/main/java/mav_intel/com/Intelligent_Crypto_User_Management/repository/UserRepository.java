package mav_intel.com.Intelligent_Crypto_User_Management.repository;

import mav_intel.com.Intelligent_Crypto_User_Management.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User,Long> {
    Optional<User> findByUsername(String username);
}
